"""No paid requests; exercise the private-path barrier and model response validation."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from run_optional_ai_review import private_output_path, save_private, parse_and_validate, ROOT
from ai_research_packets import build_all


class PrivateAIReviewTests(unittest.TestCase):
    def test_absolute_private_path_mandatory_outside_repo(self):
        with self.assertRaisesRegex(ValueError, "absolute output"):
            private_output_path(None)
        with self.assertRaisesRegex(ValueError, "absolute output"):
            private_output_path("work/ai-review-DLO.json")
        with self.assertRaisesRegex(ValueError, "public repository"):
            private_output_path(str(ROOT / "work" / "ai-review-DLO.json"))

    def test_non_overwriting_private_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "review.json"
            self.assertEqual(private_output_path(str(target)), target)
            save_private({"status": "requires-human-review"}, target)
            self.assertEqual(json.loads(target.read_text())["status"], "requires-human-review")
            self.assertFalse(target.stat().st_mode & 0o077)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                private_output_path(str(target))
            with self.assertRaises(FileExistsError):
                save_private({"status": "changed"}, target)

    def test_untrusted_response_is_never_accepted_as_model_result(self):
        packet = build_all()["DLO"]
        with self.assertRaises(ValueError):
            parse_and_validate(packet, {"status": "incomplete", "output": []})
        with self.assertRaises(ValueError):
            parse_and_validate(packet, {"status": "completed", "output": []})


if __name__ == "__main__":
    unittest.main()
