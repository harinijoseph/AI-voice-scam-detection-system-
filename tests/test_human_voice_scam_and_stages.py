import unittest
import numpy as np
from src.nlp.behavioral_analyzer import BehavioralAnalyzer
from src.nlp.content_engine import ContentEngine
from src.fusion.fusion_engine import Phase4FusionEngine
from backend.routes.analyze import format_plain_english_verdict

class TestHumanVoiceScamAndStages(unittest.TestCase):
    def setUp(self):
        self.beh = BehavioralAnalyzer()
        self.cnt = ContentEngine()
        self.fusion = Phase4FusionEngine()

    def test_no_greeting_jump_to_bail_triggers_stage_4(self):
        """When transcript contains no greeting and demands bail money, Stage 1 must NOT be active, and Stage 4 must be active."""
        transcript = "I need $5,000 cash for bail right now! Please don't tell my parents!"
        res = self.beh.analyze_transcript(transcript)

        self.assertNotIn("Stage 1: Greeting & Persona", res["active_stages"], 
                         "Stage 1 must not be active when no greeting was spoken")
        self.assertIn("Stage 4: Action Request & Coercion", res["active_stages"],
                      "Stage 4 must be active when bail/cash is demanded")
        self.assertEqual(res["detected_stage"], "Stage 4: Action Request & Coercion",
                         "Peak stage should be Stage 4")
        self.assertTrue(any("bail" in exp.lower() or "payment" in exp.lower() for exp in res["explanations"]))

    def test_greeting_followed_by_scam_activates_both_stages(self):
        """When transcript has both greeting and financial demand, both Stage 1 and Stage 4 should be in active_stages."""
        transcript = "Hello this is the Fraud Department. Send your OTP verification code immediately."
        res = self.beh.analyze_transcript(transcript)

        self.assertIn("Stage 1: Greeting & Persona", res["active_stages"])
        self.assertIn("Stage 4: Action Request & Coercion", res["active_stages"])
        self.assertEqual(res["detected_stage"], "Stage 4: Action Request & Coercion")

    def test_pure_benign_dialogue_no_greeting(self):
        """Benign dialogue without greetings should not falsely trigger scam stages."""
        transcript = "We are going to pick up groceries at the local market."
        res = self.beh.analyze_transcript(transcript)

        self.assertEqual(len(res["active_stages"]), 0)
        self.assertEqual(res["detected_stage"], "General Dialogue / Initial Statement")
        self.assertEqual(res["detected_tactics"], [])

    def test_human_voice_with_scam_content_verdict_quadrant(self):
        """Human voice (synthetic_probability < 0.50) speaking scam words must output HUMAN VOICE SCAM verdict."""
        mock_res = {
            "overall_risk_score": 0.65,
            "acoustic_result": {
                "synthetic_probability": 0.05,
                "is_synthetic": False
            },
            "content_result": {
                "scam_probability": 0.92,
                "detected_tactics": ["FINANCIAL_TRAP"],
                "flagged_phrases": ["bail money", "wire transfer"]
            }
        }
        verdict = format_plain_english_verdict(mock_res)

        self.assertIn("HUMAN VOICE SCAM", verdict["title"])
        self.assertIn("AUTHENTIC HUMAN VOICE + ACTIVE FRAUD", verdict["badge"])
        self.assertEqual(verdict["border_color"], "#ea580c")
        self.assertIn("AUTHENTIC HUMAN", verdict["summary"])
        self.assertIn("ACTIVE COERCIVE FRAUD", verdict["summary"])

    def test_ai_voice_with_scam_content_verdict_quadrant(self):
        """AI voice (synthetic_probability >= 0.50) speaking scam words must output AI VOICE CLONE & SCAM."""
        mock_res = {
            "overall_risk_score": 0.88,
            "acoustic_result": {
                "synthetic_probability": 0.95,
                "is_synthetic": True
            },
            "content_result": {
                "scam_probability": 0.85,
                "detected_tactics": ["FINANCIAL_TRAP"],
                "flagged_phrases": ["gift card"]
            }
        }
        verdict = format_plain_english_verdict(mock_res)

        self.assertIn("AI VOICE CLONE & SCAM", verdict["title"])
        self.assertEqual(verdict["border_color"], "#dc2626")

    def test_ai_voice_with_benign_content_verdict_quadrant(self):
        """AI voice with benign content must output AI SYNTHESIZED VOICE (NO SCAM DETECTED)."""
        mock_res = {
            "overall_risk_score": 0.48,
            "acoustic_result": {
                "synthetic_probability": 0.95,
                "is_synthetic": True
            },
            "content_result": {
                "scam_probability": 0.02,
                "detected_tactics": [],
                "flagged_phrases": []
            }
        }
        verdict = format_plain_english_verdict(mock_res)

        self.assertIn("AI SYNTHESIZED VOICE", verdict["title"])
        self.assertIn("NO SCAM DETECTED", verdict["title"])
        self.assertEqual(verdict["border_color"], "#7c3aed")

    def test_human_voice_with_benign_content_verdict_quadrant(self):
        """Human voice with benign content must output AUTHENTIC HUMAN VOICE (SAFE)."""
        mock_res = {
            "overall_risk_score": 0.10,
            "acoustic_result": {
                "synthetic_probability": 0.08,
                "is_synthetic": False
            },
            "content_result": {
                "scam_probability": 0.05,
                "detected_tactics": [],
                "flagged_phrases": []
            }
        }
        verdict = format_plain_english_verdict(mock_res)

        self.assertIn("AUTHENTIC HUMAN VOICE (SAFE)", verdict["title"])
        self.assertEqual(verdict["border_color"], "#16a34a")

if __name__ == "__main__":
    unittest.main()
