import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import unittest
from src.utils.sample_generator import generate_demo_samples
from src.fusion.fusion_engine import Phase4FusionEngine

class TestPhase4FusionAndDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = generate_demo_samples(output_dir="data")
        cls.engine = Phase4FusionEngine(w_acoustic=0.50, w_content=0.50)

    def test_fusion_evaluation_legitimate(self):
        legit_info = self.samples["Legitimate Family Call"]
        res = self.engine.analyze_audio_call(legit_info["file"], optional_transcript=legit_info["transcript"])
        
        self.assertIn("overall_risk_score", res)
        self.assertIn("engine_breakdown", res)
        self.assertIn("visuals", res)
        self.assertLess(res["overall_risk_score"], 0.50)
        self.assertEqual(res["risk_category"], "LOW RISK / AUTHENTIC")

    def test_fusion_evaluation_scam(self):
        scam_info = self.samples["AI Cloned Emergency Scam (Grandparent Trap)"]
        res = self.engine.analyze_audio_call(scam_info["file"], optional_transcript=scam_info["transcript"])
        
        self.assertGreaterEqual(res["overall_risk_score"], 0.50)
        self.assertTrue(res["challenge_triggered"])
        self.assertIsNotNone(res["challenge_prompt"])
        self.assertIn("Family Emergency & Bail Scam", res["content_result"]["category"])
        self.assertIn("detected_tactics", res["content_result"])
        self.assertIn("detected_stage", res["content_result"])

if __name__ == "__main__":
    unittest.main()
