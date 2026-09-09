import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifacts import build_artifact_pdf
from paths import downloads_dir, save_to_downloads


class DownloadTests(unittest.TestCase):
    def test_all_supported_formats_are_saved_to_downloads(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(os.environ, {"TASKLOOM_DOWNLOADS_DIR": temporary_directory}):
                markdown_path = save_to_downloads("# Result", "Taskloom-approved-output.md")
                text_path = save_to_downloads("Result", "Taskloom-approved-output.txt")
                pdf_path = save_to_downloads(
                    build_artifact_pdf("# Result"), "Taskloom-approved-output.pdf"
                )

                expected_folder = Path(temporary_directory)
                self.assertEqual(downloads_dir(), expected_folder)
                self.assertEqual(markdown_path.parent, expected_folder)
                self.assertEqual(text_path.parent, expected_folder)
                self.assertEqual(pdf_path.parent, expected_folder)
                self.assertEqual(markdown_path.read_text(encoding="utf-8"), "# Result")
                self.assertEqual(text_path.read_text(encoding="utf-8"), "Result")
                self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))

    def test_existing_download_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(os.environ, {"TASKLOOM_DOWNLOADS_DIR": temporary_directory}):
                first = save_to_downloads("first", "Taskloom-approved-output.txt")
                second = save_to_downloads("second", "Taskloom-approved-output.txt")

                self.assertNotEqual(first, second)
                self.assertEqual(first.read_text(encoding="utf-8"), "first")
                self.assertEqual(second.read_text(encoding="utf-8"), "second")
                self.assertEqual(second.name, "Taskloom-approved-output (1).txt")


if __name__ == "__main__":
    unittest.main()
