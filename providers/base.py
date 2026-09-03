from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    name = "base"

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        raise NotImplementedError

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

