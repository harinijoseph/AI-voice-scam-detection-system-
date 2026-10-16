import os
import sys
import unittest
import numpy as np
import librosa
import torch

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.audio.feature_extractor import extract_acoustic_features
from src.audio.acoustic_analyzer import AcousticAnalyzer
from src.audio.acoustic_visualizer import plot_pitch_contour, plot_mel_spectrogram_with_anomalies, generate_acoustic_visuals
from src.nlp.behavioral_analyzer import BehavioralAnalyzer
from src.nlp.content_engine import ContentEngine
from src.fusion.fusion_engine import Phase4FusionEngine
from src.utils.sample_generator import generate_demo_samples


class TestAudioFeatureExtractorRobustness(unittest.TestCase):
    """Evaluates acoustic feature extraction across critical edge cases and malformed inputs."""

    def test_silent_audio_features(self):
        """Verify feature extraction survives completely silent audio (all zeros) without NaNs/Infs."""
        y_silent = np.zeros(16000, dtype=np.float32)
        vec, names = extract_acoustic_features(y_silent, sr=16000)
        
        self.assertEqual(len(vec), 400)
        self.assertEqual(len(vec), len(names))
        self.assertFalse(np.isnan(vec).any(), "Silent audio produced NaNs in feature vector")
        self.assertFalse(np.isinf(vec).any(), "Silent audio produced Infs in feature vector")

    def test_extremely_short_clip(self):
        """Verify feature extraction survives very short clips (< 0.5s) via zero-padding."""
        # 100 samples ~ 0.006 seconds
        y_short = np.array([0.1, -0.15, 0.2, -0.05] * 25, dtype=np.float32)
        vec, names = extract_acoustic_features(y_short, sr=16000)
        
        self.assertEqual(len(vec), 400)
        self.assertFalse(np.isnan(vec).any())
        self.assertFalse(np.isinf(vec).any())

    def test_stereo_multichannel_downmix(self):
        """Verify 2-channel stereo audio is safely downmixed to mono without dimensional explosion."""
        y_stereo = np.random.normal(0, 0.1, (2, 16000)).astype(np.float32)
        vec, names = extract_acoustic_features(y_stereo, sr=16000)
        
        self.assertEqual(len(vec), 400)
        self.assertFalse(np.isnan(vec).any())

    def test_corrupted_nan_inf_audio(self):
        """Verify inputs with NaNs and infinities are sanitized to finite numbers."""
        y_corrupt = np.array([np.nan, np.inf, -np.inf, 0.25, -0.15] * 3200, dtype=np.float32)
        vec, names = extract_acoustic_features(y_corrupt, sr=16000)
        
        self.assertEqual(len(vec), 400)
        self.assertFalse(np.isnan(vec).any())
        self.assertFalse(np.isinf(vec).any())

    def test_empty_audio_raises_error(self):
        """Verify empty audio or None raises ValueError explicitly."""
        with self.assertRaises(ValueError):
            extract_acoustic_features(np.array([], dtype=np.float32))

        with self.assertRaises(ValueError):
            extract_acoustic_features(None)


class TestAcousticAnalyzerQualityAndFallbacks(unittest.TestCase):
    """Evaluates forensic acoustic engine inference, edge cases, and graceful model fallbacks."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = AcousticAnalyzer()

    def test_analyzer_model_attributes_loaded(self):
        """Ensure standard attributes expected by evaluation scripts exist."""
        self.assertTrue(hasattr(self.analyzer, "model"))
        self.assertTrue(hasattr(self.analyzer, "scaler"))
        self.assertTrue(hasattr(self.analyzer, "device"))
        self.assertTrue(self.analyzer.is_trained)

    def test_missing_model_fallback(self):
        """Ensure analyzer gracefully handles missing or invalid model paths without crashing."""
        fallback_analyzer = AcousticAnalyzer(
            model_path="nonexistent_model.pth",
            scaler_path="nonexistent_scaler.pkl"
        )
        self.assertFalse(fallback_analyzer.is_trained)
        self.assertIsNone(fallback_analyzer.model)
        self.assertIsNone(fallback_analyzer.scaler)

        # Still analyzes audio via heuristic fallback
        y_test = np.sin(2 * np.pi * 220 * np.linspace(0, 1, 16000)).astype(np.float32)
        res = fallback_analyzer.analyze_audio_file(y_test)
        self.assertIn("synthetic_probability", res)
        self.assertIn("is_synthetic", res)
        self.assertIn("explanations", res)

    def test_silent_audio_detection(self):
        """Completely silent audio should be classified as low synthetic risk with silence note."""
        y_silent = np.zeros(16000, dtype=np.float32)
        res = self.analyzer.analyze_audio_file(y_silent)
        
        self.assertLessEqual(res["synthetic_probability"], 0.10)
        self.assertFalse(res["is_synthetic"])
        self.assertTrue(any("silent" in exp.lower() for exp in res["explanations"]))

    def test_pure_static_noise_detection(self):
        """Pure Gaussian white noise should be identified as ambient noise without human speech."""
        np.random.seed(42)
        y_noise = np.random.normal(0, 0.5, 16000).astype(np.float32)
        res = self.analyzer.analyze_audio_file(y_noise)
        
        self.assertLessEqual(res["synthetic_probability"], 0.25)
        self.assertFalse(res["is_synthetic"])
        self.assertTrue(any("noise" in exp.lower() or "static" in exp.lower() for exp in res["explanations"]))

    def test_conformer_neural_inference_accuracy(self):
        """Verify loaded Conformer accurately distinguishes real speech from synthetic deepfakes."""
        import glob
        dataset_human = sorted(glob.glob(os.path.join(PROJECT_ROOT, "human-nonhuman", "human", "*.mp3")))
        dataset_nonhuman = sorted(glob.glob(os.path.join(PROJECT_ROOT, "human-nonhuman", "nonhuman", "*.mp3")))
        if dataset_human and dataset_nonhuman:
            real_clip = dataset_human[4]
            fake_clip = dataset_nonhuman[0]
        else:
            real_clip = os.path.join(PROJECT_ROOT, "data", "phase1", "real", "real_clip_001.wav")
            fake_clip = os.path.join(PROJECT_ROOT, "data", "phase1", "fake", "fake_clip_001.wav")

        if os.path.exists(real_clip) and os.path.exists(fake_clip):
            res_real = self.analyzer.analyze_audio_file(real_clip)
            res_fake = self.analyzer.analyze_audio_file(fake_clip)

            self.assertLess(res_real["synthetic_probability"], 0.50, "Real clip should have low synthetic prob")
            self.assertGreaterEqual(res_fake["synthetic_probability"], 0.50, "Fake clip should have high synthetic prob")
            self.assertFalse(res_real["is_synthetic"])
            self.assertTrue(res_fake["is_synthetic"])


class TestBehavioralNLPAdvancedPatterns(unittest.TestCase):
    """Evaluates behavioral NLP heuristics, expanded scam triggers, and multi-turn funnel scoring."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = BehavioralAnalyzer()

    def test_cryptocurrency_and_wire_triggers(self):
        text = "Deposit $1000 into this Bitcoin ATM wallet address right now to unlock your account."
        res = self.analyzer.analyze_transcript(text)

        self.assertIn("FINANCIAL_TRAP", res["detected_tactics"])
        self.assertGreaterEqual(res["behavioral_score"], 0.70)
        self.assertEqual(res["detected_stage"], "Stage 4: Action Request & Coercion")

    def test_bail_and_law_enforcement_triggers(self):
        text = "This is Officer Reynolds. Your grandson is held in custody at the police precinct and needs bail money immediately."
        res = self.analyzer.analyze_transcript(text)

        self.assertIn("FAMILY_EMERGENCY_SCAM", res["detected_tactics"])
        self.assertIn("FINANCIAL_TRAP", res["detected_tactics"])
        self.assertGreaterEqual(res["behavioral_score"], 0.80)

    def test_credential_harvesting_and_isolation(self):
        text = "Do not hang up this call. Read back the one-time OTP verification code and SSN right now."
        res = self.analyzer.analyze_transcript(text)

        self.assertIn("CREDENTIAL_HARVEST", res["detected_tactics"])
        self.assertIn("ISOLATION_TACTIC", res["detected_tactics"])
        self.assertGreaterEqual(res["behavioral_score"], 0.80)

    def test_tech_remote_takeover(self):
        text = "Critical malware virus detected. Download AnyDesk immediately and grant remote access to your computer."
        res = self.analyzer.analyze_transcript(text)

        self.assertIn("TECH_REMOTE_TAKEOVER", res["detected_tactics"])
        self.assertGreaterEqual(res["behavioral_score"], 0.70)

    def test_utility_disconnection_threat(self):
        text = "Electric power service will be disconnected in 30 minutes due to unpaid utility bills. Pay immediately."
        res = self.analyzer.analyze_transcript(text)

        self.assertIn("UTILITY_SHUTOFF_COERCION", res["detected_tactics"])
        self.assertGreaterEqual(res["behavioral_score"], 0.70)

    def test_multi_turn_stage_progression_scoring(self):
        """Conversations progressing across all 4 stages should score higher than single-stage text."""
        single_stage = "Hello, calling from customer support."
        full_progression = (
            "Hello, this is Officer Davis calling from the fraud prevention department. "
            "Your bank account has been compromised in a severe criminal investigation. "
            "You must act immediately right now before the police arrive. "
            "Send money via wire transfer right now to secure your funds."
        )

        res_single = self.analyzer.analyze_transcript(single_stage)
        res_full = self.analyzer.analyze_transcript(full_progression)

        self.assertLess(res_single["behavioral_score"], 0.20)
        self.assertGreaterEqual(res_full["behavioral_score"], 0.85)

    def test_benign_conversational_text_scores_low(self):
        benign_texts = [
            "Hi, just calling to see what time we are meeting for lunch today.",
            "Can you email me the slides for the engineering presentation?",
            "Good morning! Hope you had a wonderful weekend with the family."
        ]
        for text in benign_texts:
            res = self.analyzer.analyze_transcript(text)
            self.assertLessEqual(res["behavioral_score"], 0.15, f"Benign text scored too high: {text}")
            self.assertEqual(len(res["detected_tactics"]), 0)


class TestContentEngineResilience(unittest.TestCase):
    """Evaluates ContentEngine categorization, keyword markup, and input resilience."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ContentEngine()

    def test_empty_or_whitespace_transcript(self):
        res = self.engine.analyze_text("   ")
        self.assertEqual(res["scam_probability"], 0.0)
        self.assertFalse(res["is_scam"])
        self.assertEqual(res["category"], "Authentic / Normal Dialogue")

    def test_cryptocurrency_fraud_categorization(self):
        text = "Guaranteed 10x ROI investment opportunity. Send Bitcoin to this wallet address immediately."
        res = self.engine.analyze_text(text)
        self.assertTrue(res["is_scam"])
        self.assertIn("Cryptocurrency", res["category"])
        self.assertGreaterEqual(res["scam_probability"], 0.65)

    def test_highlighted_transcript_markup(self):
        text = "Send a wire transfer and your OTP code right now."
        res = self.engine.analyze_text(text)
        self.assertIn('<span class="badge-keyword"', res["highlighted_transcript"])
        self.assertIn("wire transfer", res["flagged_phrases"])


class TestFusionEngineCalibrationAndEdgeCases(unittest.TestCase):
    """Evaluates fusion calibration, risk thresholds, breakdowns, and defenses."""

    @classmethod
    def setUpClass(cls):
        cls.fusion = Phase4FusionEngine(w_acoustic=0.50, w_content=0.50)
        cls.samples = generate_demo_samples("data")

    def test_legitimate_call_calibrated_low(self):
        legit = self.samples["Legitimate Family Call"]
        res = self.fusion.analyze_audio_call(legit["file"], optional_transcript=legit["transcript"])
        
        self.assertLess(res["overall_risk_score"], 0.35, "Legitimate call must have calibrated low risk")
        self.assertEqual(res["risk_category"], "LOW RISK / AUTHENTIC")
        self.assertFalse(res["challenge_triggered"])

    def test_emergency_scam_call_calibrated_high(self):
        scam = self.samples["AI Cloned Emergency Scam (Grandparent Trap)"]
        res = self.fusion.analyze_audio_call(scam["file"], optional_transcript=scam["transcript"])

        self.assertGreaterEqual(res["overall_risk_score"], 0.70, "High-threat emergency scam must score >= 0.70")
        self.assertEqual(res["risk_category"], "HIGH RISK / AI SCAM DETECTED")
        self.assertTrue(res["challenge_triggered"])
        self.assertIsNotNone(res["challenge_prompt"])

    def test_custom_fusion_weights_breakdown(self):
        custom_fusion = Phase4FusionEngine(w_acoustic=0.70, w_content=0.30)
        legit = self.samples["Legitimate Family Call"]
        res = custom_fusion.analyze_audio_call(legit["file"], optional_transcript=legit["transcript"])

        breakdown = res["engine_breakdown"]
        self.assertEqual(breakdown["w_acoustic"], 0.70)
        self.assertEqual(breakdown["w_content"], 0.30)
        self.assertAlmostEqual(
            res["overall_risk_score"],
            breakdown["acoustic_contribution"] + breakdown["content_contribution"],
            places=2
        )


class TestAudioBackendHardening(unittest.TestCase):
    """Rigorous auditing and stress-testing for VoxSentinel AI Audio Backend."""

    @classmethod
    def setUpClass(cls):
        cls.content_engine = ContentEngine()
        cls.acoustic_analyzer = AcousticAnalyzer()
        cls.fusion_engine = Phase4FusionEngine()

    def test_transcribe_audio_numpy_array_and_fallbacks(self):
        """transcribe_audio accepts numpy arrays and safely falls back on silent/invalid input."""
        # Silent numpy array
        silent_arr = np.zeros(16000, dtype=np.float32)
        res_silent = self.content_engine.transcribe_audio(silent_arr)
        self.assertEqual(res_silent, "")

        # Empty numpy array
        res_empty = self.content_engine.transcribe_audio(np.array([], dtype=np.float32))
        self.assertEqual(res_empty, "")

        # None input
        res_none = self.content_engine.transcribe_audio(None)
        self.assertEqual(res_none, "")

        # Non-existent file path
        res_nonexistent = self.content_engine.transcribe_audio("nonexistent_audio_file.wav")
        self.assertEqual(res_nonexistent, "")

        # Very short clip
        res_short = self.content_engine.transcribe_audio(np.random.normal(0, 0.1, 50).astype(np.float32))
        self.assertEqual(res_short, "")

    def test_analyze_audio_content_silent_and_empty(self):
        """analyze_audio_content never crashes on empty, silent, or array inputs."""
        res_empty = self.content_engine.analyze_audio_content(np.array([], dtype=np.float32))
        self.assertIn("scam_probability", res_empty)
        self.assertFalse(res_empty["is_scam"])

        res_silent = self.content_engine.analyze_audio_content(np.zeros(16000, dtype=np.float32))
        self.assertIn("category", res_silent)
        self.assertEqual(res_silent["scam_probability"], 0.0)

    def test_acoustic_analyzer_telemetry_features_finite_real(self):
        """All telemetry features in feature_summary must always be finite real numbers."""
        test_inputs = [
            np.zeros(16000, dtype=np.float32),  # Silence
            np.array([0.05, -0.05] * 50, dtype=np.float32),  # Short clip (< 0.5s)
            np.random.normal(0, 0.3, 16000).astype(np.float32),  # Static noise
            np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32),  # Sine wave
            np.array([], dtype=np.float32)  # Empty array
        ]

        telemetry_keys = [
            "pitch_jitter", "shimmer", "centroid", "flatness", "zcr",
            "inst_freq_std", "spec_entropy_std", "spec_flux_mean", "delta_mfcc_std"
        ]

        for audio_input in test_inputs:
            res = self.acoustic_analyzer.analyze_audio_file(audio_input)
            self.assertIn("synthetic_probability", res)
            self.assertGreaterEqual(res["synthetic_probability"], 0.0)
            self.assertLessEqual(res["synthetic_probability"], 1.0)
            self.assertIn("feature_summary", res)
            feat_summary = res["feature_summary"]

            for key in telemetry_keys:
                self.assertIn(key, feat_summary, f"Key '{key}' missing from feature_summary")
                val = feat_summary[key]
                self.assertIsInstance(val, (int, float), f"Key '{key}' is not numeric")
                self.assertTrue(np.isfinite(val), f"Key '{key}' with value {val} is not finite")

    def test_acoustic_visualizer_silent_constant_short(self):
        """plot_pitch_contour and plot_mel_spectrogram_with_anomalies never fail on extreme audio."""
        extreme_inputs = [
            np.zeros(16000, dtype=np.float32),  # Completely silent
            np.ones(16000, dtype=np.float32) * 0.5,  # Constant DC offset
            np.array([0.1, -0.1] * 25, dtype=np.float32),  # Extremely short (50 samples)
            np.zeros(10, dtype=np.float32)  # Very short silent (10 samples)
        ]

        for y in extreme_inputs:
            pitch_fig, pitch_metrics = plot_pitch_contour(y, sr=22050)
            self.assertIsNotNone(pitch_fig)
            self.assertIn("f0_mean", pitch_metrics)
            self.assertIn("f0_std", pitch_metrics)
            self.assertTrue(np.isfinite(pitch_metrics["f0_mean"]))
            self.assertTrue(np.isfinite(pitch_metrics["f0_std"]))

            spec_fig, spec_metrics = plot_mel_spectrogram_with_anomalies(y, sr=22050)
            self.assertIsNotNone(spec_fig)
            self.assertIn("anomaly_frame_count", spec_metrics)
            self.assertIn("total_frames", spec_metrics)
            self.assertGreaterEqual(spec_metrics["total_frames"], 1)

    def test_fusion_engine_defensive_completeness(self):
        """analyze_audio_call always returns a complete valid dictionary even on extreme inputs."""
        expected_keys = [
            "overall_risk_score", "risk_category", "acoustic_result",
            "content_result", "visuals", "engine_breakdown", "explanations",
            "challenge_triggered", "challenge_prompt"
        ]

        # Test with silent numpy array
        res_silent = self.fusion_engine.analyze_audio_call(np.zeros(16000, dtype=np.float32))
        for key in expected_keys:
            self.assertIn(key, res_silent, f"Missing key in fusion output: {key}")
        self.assertGreaterEqual(res_silent["overall_risk_score"], 0.0)
        self.assertLessEqual(res_silent["overall_risk_score"], 1.0)

        # Test with extremely short array
        res_short = self.fusion_engine.analyze_audio_call(np.array([0.05, -0.05] * 20, dtype=np.float32))
        for key in expected_keys:
            self.assertIn(key, res_short, f"Missing key in fusion output: {key}")

        # Test with mocked failing acoustic analyzer
        original_analyze = self.fusion_engine.acoustic_analyzer.analyze_audio_file
        try:
            self.fusion_engine.acoustic_analyzer.analyze_audio_file = lambda *args, **kwargs: 1 / 0
            res_fail = self.fusion_engine.analyze_audio_call(np.zeros(16000, dtype=np.float32))
            for key in expected_keys:
                self.assertIn(key, res_fail, f"Missing key under acoustic failure: {key}")
            self.assertGreaterEqual(res_fail["overall_risk_score"], 0.0)
            self.assertLessEqual(res_fail["overall_risk_score"], 1.0)
        finally:
            self.fusion_engine.acoustic_analyzer.analyze_audio_file = original_analyze


if __name__ == "__main__":
    unittest.main()
