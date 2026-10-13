from __future__ import annotations

import asyncio
import hashlib
import time
from datetime import datetime
from typing import TypeVar

from diskcache import Cache
from pydantic import BaseModel

from paths import application_data_dir
from .base import LLMProvider

T = TypeVar("T", bound=BaseModel)


def is_rate_limit_error(exc: Exception) -> bool:
    """Return whether Gemini rejected a request because capacity/quota was exhausted."""
    details = str(exc).lower()
    return any(marker in details for marker in ("429", "resource_exhausted", "rate limit", "quota"))


def is_temporary_provider_error(exc: Exception) -> bool:
    details = str(exc).lower()
    return any(marker in details for marker in ("503", "504", "unavailable", "deadline_exceeded"))


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing.")
        from google import genai
        from google.genai import types

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=120_000,
                retry_options=types.HttpRetryOptions(
                    attempts=1,
                    initial_delay=0.5,
                    max_delay=2.0,
                ),
            ),
        )
        self.model = model
        self.types = types
        cache_dir = application_data_dir() / "cache"
        self.cache = Cache(str(cache_dir))
        self.last_call_cached = False
        self.last_call_kind = ""

    def _usage_key(self) -> str:
        day = datetime.now().astimezone().date().isoformat()
        return f"usage:{day}:{self.model}:successful_requests"

    def _record_api_success(self) -> None:
        key = self._usage_key()
        with self.cache.transact():
            self.cache.set(key, int(self.cache.get(key, 0)) + 1, expire=172_800)

    def successful_requests_today(self) -> int:
        """Local estimate only; Google remains authoritative for quota usage."""
        return int(self.cache.get(self._usage_key(), 0))

    def _cache_key(self, response_type: str, prompt: str, schema_name: str = "") -> str:
        material = f"{self.model}\0{response_type}\0{schema_name}\0{prompt}".encode("utf-8")
        return "gemini:" + hashlib.sha256(material).hexdigest()

    @staticmethod
    def _retry_temporary(call):
        for attempt in range(3):
            try:
                return call()
            except Exception as exc:
                if attempt == 2 or not is_temporary_provider_error(exc):
                    raise
                time.sleep(1.5 * (2 ** attempt))

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        self.last_call_kind = "preview"
        cache_key = self._cache_key("structured", prompt, schema.__name__)
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_call_cached = True
            return schema.model_validate_json(cached)

        self.last_call_cached = False

        def call() -> T:
            # Keep the request compact: native schema mode currently rejects
            # semantic_frame's open-ended object, and large schemas can trigger
            # provider overload before any response is generated.
            shape = (
                '{"analysis":{"original_text":"","normalized_text":"","intent":""},'
                '"plan":{"goal":"","tasks":[{"id":"task_1","title":"",'
                '"objective":"","assigned_role":"Specific Specialist",'
                '"dependencies":[]}]},"worker_results":[{"task_id":"task_1",'
                '"title":"","content":""}],"review":{"approved":true,'
                '"score":8,"strengths":[],"issues":[]},"final_answer":""}'
            )
            response = self._retry_temporary(lambda: self.client.models.generate_content(
                model=self.model,
                contents=f"{prompt}\n\nReturn ONLY one valid JSON object in this shape, filling every value with task-specific content: {shape}",
                config=self.types.GenerateContentConfig(
                    automatic_function_calling=self.types.AutomaticFunctionCallingConfig(disable=True),
                ),
            ))
            if not response.text:
                raise ValueError("Gemini returned an empty structured response.")
            payload = response.text.strip()
            if payload.startswith("```json"):
                payload = payload[7:]
            elif payload.startswith("```"):
                payload = payload[3:]
            if payload.endswith("```"):
                payload = payload[:-3]
            validated = schema.model_validate_json(payload.strip())
            self.cache.set(cache_key, validated.model_dump_json(), expire=604_800)
            self._record_api_success()
            return validated

        return await asyncio.to_thread(call)

    async def generate_text(self, prompt: str) -> str:
        self.last_call_kind = "revision"
        cache_key = self._cache_key("text", prompt)
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_call_cached = True
            return cached

        self.last_call_cached = False

        def call() -> str:
            response = self._retry_temporary(lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    automatic_function_calling=self.types.AutomaticFunctionCallingConfig(disable=True),
                ),
            ))
            if not response.text:
                raise ValueError("Gemini returned an empty text response.")
            self.cache.set(cache_key, response.text, expire=604_800)
            self._record_api_success()
            return response.text

        return await asyncio.to_thread(call)


class GeminiFailoverProvider(LLMProvider):
    """Try the primary Gemini key first and use a spare only for rate limits."""

    name = "gemini"

    def __init__(self, api_keys: list[str], model: str):
        unique_keys = list(dict.fromkeys(key.strip() for key in api_keys if key and key.strip()))
        if not unique_keys:
            raise ValueError("GEMINI_API_KEY is missing.")
        self.providers = [GeminiProvider(key, model) for key in unique_keys]
        self.last_call_cached = False
        self.last_call_kind = ""
        self.used_backup_key = False

    async def _request(self, method: str, *args):
        self.used_backup_key = False
        last_rate_limit: Exception | None = None

        for index, provider in enumerate(self.providers):
            try:
                response = await getattr(provider, method)(*args)
            except Exception as exc:
                if not is_rate_limit_error(exc):
                    raise
                last_rate_limit = exc
                continue

            self.last_call_cached = provider.last_call_cached
            self.last_call_kind = provider.last_call_kind
            self.used_backup_key = index > 0
            return response

        raise RuntimeError(
            "Gemini returned 429 for every configured API key. "
            f"Last provider response: {last_rate_limit}"
        ) from last_rate_limit

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        return await self._request("generate_structured", prompt, schema)

    async def generate_text(self, prompt: str) -> str:
        return await self._request("generate_text", prompt)

    def successful_requests_today(self) -> int:
        """Both providers share the same local cache-backed usage counter."""
        return self.providers[0].successful_requests_today()
