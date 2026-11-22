import tempfile
import unittest
from pathlib import Path
import cv2

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from generate_textures import generate_set


class TextureTests(unittest.TestCase):
    def test_generated_maps_and_iris_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            uv = root / "textures" / "uv_maps"
            info = generate_set(1, uv, 256)
            albedo = cv2.imread(str(uv / "subject_01_albedo.png"), cv2.IMREAD_UNCHANGED)
            roughness = cv2.imread(str(uv / "subject_01_roughness.png"), cv2.IMREAD_UNCHANGED)
            bump = cv2.imread(str(uv / "subject_01_bump.png"), cv2.IMREAD_UNCHANGED)
            left = cv2.imread(str(root / "textures" / "iris_maps" / "subject_01_iris_L.png"))
            right = cv2.imread(str(root / "textures" / "iris_maps" / "subject_01_iris_R.png"))
            self.assertIsNotNone(albedo)
            self.assertEqual(albedo.shape[:2], (256, 256))
            self.assertIsNotNone(roughness)
            self.assertIsNotNone(bump)
            self.assertIsNotNone(left)
            self.assertIsNotNone(right)
            self.assertGreater(cv2.absdiff(left, right).mean(), 0.0)
            self.assertEqual(info["size"], 256)
