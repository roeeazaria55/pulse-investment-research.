import tempfile
import unittest
from pathlib import Path
from test_research_bundle import ResearchBundleTests
from stage_research_bundle import stage_bundle


class ResearchStagingTests(unittest.TestCase):
    def test_stage_validated_sources_without_modifying_repository(self):
        pack=ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as directory:
                destination=Path(directory)/"stage"
                self.assertEqual(stage_bundle(str(pack),str(destination)),7)
                self.assertTrue((destination/"originals/Source0.pdf").exists())
                self.assertTrue((destination/"extracted/T0.pages.json").exists())
                self.assertTrue((destination/"manifest.json").exists())
        finally:
            pack.unlink()


if __name__=="__main__":
    unittest.main()
