import unittest

from comparison import build_direct_gemini_prompt, output_statistics


class ComparisonTests(unittest.TestCase):
    def test_direct_prompt_preserves_the_user_request(self):
        request = "Write a two-paragraph welcome note."
        prompt = build_direct_gemini_prompt(request)

        self.assertIn(request, prompt)
        self.assertIn("Return only the finished response", prompt)

    def test_output_statistics_are_deterministic(self):
        statistics = output_statistics("First paragraph.\n\nSecond paragraph has four words.")

        self.assertEqual(statistics.words, 7)
        self.assertEqual(statistics.paragraphs, 2)
        self.assertEqual(statistics.characters, 50)


if __name__ == "__main__":
    unittest.main()
