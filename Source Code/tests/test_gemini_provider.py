from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from pydantic import BaseModel

from providers.gemini import GeminiProvider, is_temporary_provider_error


class SmallResult(BaseModel):
    answer: str


class GeminiProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_preview_uses_generate_content_and_validates_json(self):
        with patch("providers.gemini.Cache") as cache_class:
            cache_class.return_value.get.side_effect = lambda _key, default=None: default
            provider = GeminiProvider("test-key", "test-model")
            provider.client.models.generate_content = Mock(
                return_value=Mock(text='```json\n{"answer":"ready"}\n```')
            )
            result = await provider.generate_structured("test request", SmallResult)

        self.assertEqual(result.answer, "ready")
        self.assertEqual(provider.client.models.generate_content.call_count, 1)
        self.assertFalse(provider.last_call_cached)

    def test_temporary_error_retries_but_quota_error_does_not(self):
        call = Mock(side_effect=[RuntimeError("503 UNAVAILABLE"), "ready"])
        with patch("providers.gemini.time.sleep") as delay:
            self.assertEqual(GeminiProvider._retry_temporary(call), "ready")
        self.assertEqual(call.call_count, 2)
        delay.assert_called_once()

        call = Mock(side_effect=RuntimeError("429 quota_exceeded"))
        with self.assertRaisesRegex(RuntimeError, "429"):
            GeminiProvider._retry_temporary(call)
        self.assertEqual(call.call_count, 1)
        self.assertFalse(is_temporary_provider_error(RuntimeError("429 quota_exceeded")))


if __name__ == "__main__":
    unittest.main()
