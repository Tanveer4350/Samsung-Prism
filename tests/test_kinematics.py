import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kinematics_engine import GazeEngine


class KinematicsTests(unittest.TestCase):
    def test_gaze_limits_and_blink_duration(self):
        engine = GazeEngine(30)
        samples = engine.plan("Left", 4.0)
        self.assertEqual(len(samples), 121)
        self.assertGreaterEqual(min(s.yaw for s in samples), -35.0)
        self.assertLessEqual(max(s.yaw for s in samples), 35.0)
        self.assertGreaterEqual(min(s.pitch for s in samples), -30.0)
        self.assertLessEqual(max(s.pitch for s in samples), 25.0)
        blink_frames = sum(1 for s in samples if s.blink > 0)
        self.assertLessEqual(blink_frames, 6)

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            GazeEngine().plan("Right", 16.0)
