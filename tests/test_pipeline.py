import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_missing_texture_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.png"
            with self.assertRaises(SystemExit):
                run_pipeline.main(["--input", "Left", "--texture", str(missing)])

    def test_missing_model_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.obj"
            with self.assertRaises(SystemExit):
                run_pipeline.main(["--input", "Right", "--model", str(missing)])

    def test_duration_limit_and_blend_exists(self):
        with self.assertRaises(SystemExit):
            run_pipeline.main(["--input", "Left", "--duration", "16"])
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "blend_files" / "synthetic_head_rig.blend").exists())
