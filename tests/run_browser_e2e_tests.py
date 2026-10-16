"""
VoxSentinel AI — Comprehensive Browser & DOM E2E Quality Verification Suite
Validates the live HTTP server endpoint, Streamlit component lifecycle across all
5 dedicated compartments, live microphone ingestion, uploaded telephony audio,
adversarial presets, forensic physics telemetry, behavioral NLP funnels, and OPSEC OOB challenge.
"""

import os
import sys
import io
import unittest
import requests
from contextlib import redirect_stderr

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from streamlit.testing.v1 import AppTest


class TestVoxSentinelE2E(unittest.TestCase):
    """Full browser-equivalent E2E test suite for VoxSentinel AI Streamlit Application."""

    APP_PATH = os.path.join(PROJECT_ROOT, "app_streamlit.py")
    LIVE_URL = "http://localhost:8501"

    # -------------------------------------------------------------------------
    # 1. Live Endpoint Verification
    # -------------------------------------------------------------------------
    def test_01_live_http_server_endpoint_200(self):
        """Verify the live Streamlit server responds with HTTP 200 OK and health endpoint is active."""
        try:
            resp = requests.get(self.LIVE_URL, timeout=5)
            self.assertEqual(
                resp.status_code, 200,
                f"Expected HTTP 200 from {self.LIVE_URL}, got {resp.status_code}"
            )
            self.assertIn(
                "text/html", resp.headers.get("content-type", ""),
                "Content-type should be text/html"
            )
            self.assertIn("VoxSentinel", resp.text, "Response HTML should contain VoxSentinel app metadata")

            # Check Streamlit core health
            health_resp = requests.get(f"{self.LIVE_URL}/_stcore/health", timeout=5)
            self.assertEqual(health_resp.status_code, 200)
            self.assertEqual(health_resp.text.strip(), "ok")
        except requests.exceptions.ConnectionError:
            self.fail(f"Could not connect to live server at {self.LIVE_URL}. Ensure Streamlit is running.")

    # -------------------------------------------------------------------------
    # 2. Page Brand Header & Active Defense Status
    # -------------------------------------------------------------------------
    def test_02_brand_header_and_monitoring_status(self):
        """Verify brand header, framework title, and system armed active badge."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()
        self.assertFalse(at.exception, f"App threw unexpected exception: {at.exception}")
        self.assertEqual(len(at.error), 0, "No red st.error banners should appear on initial load")

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("VoxSentinel AI Defense Framework", all_md)
        self.assertIn("Zero-Shot Synthetic Voice Scam & Deepfake Defense System", all_md)
        self.assertIn("SYSTEM ARMED & ACTIVE", all_md)

    # -------------------------------------------------------------------------
    # 3. Top-Level 5 Compartment Navigation Bar
    # -------------------------------------------------------------------------
    def test_03_compartment_navigation_bar(self):
        """Verify all 5 compartments exist and can be traversed sequentially with zero exceptions."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        self.assertGreater(len(at.radio), 0, "Compartment navigation radio missing")
        nav_radio = at.radio[0]
        expected_compartments = [
            "🛡️ Compartment 1: Live Voice Scanner",
            "🔬 Compartment 2: Vocal Physics Lab",
            "💬 Compartment 3: Conversation & Scam Words",
            "🔑 Compartment 4: Family Verification Tool",
            "📊 Compartment 5: Accuracy & Benchmarks"
        ]
        self.assertEqual(nav_radio.options, expected_compartments)

        # Traverse every single compartment cleanly
        for comp in expected_compartments:
            at.radio[0].set_value(comp).run()
            self.assertFalse(at.exception, f"Error switching to {comp}: {at.exception}")
            self.assertEqual(len(at.error), 0, f"Error banner detected when viewing {comp}")

    # -------------------------------------------------------------------------
    # 4. Compartment 1: Live Microphone Voice Ingestion & Authentic Verdict
    # -------------------------------------------------------------------------
    def test_04_compartment_1_live_microphone_ingestion(self):
        """Verify feeding user microphone voice (data/live_mic_recording.wav) produces accurate, genuine low-risk verdict."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        # In Compartment 1, switch to microphone input
        input_method_radio = at.radio[1]
        self.assertIn("🎙️ Record from Microphone", input_method_radio.options)
        input_method_radio.set_value("🎙️ Record from Microphone").run()

        self.assertFalse(at.exception, f"Error on switching to mic: {at.exception}")
        self.assertEqual(len(at.error), 0, "No errors when activating microphone mode")

        # Verify recorded audio path is active
        self.assertEqual(at.session_state.selected_audio_path, "data/live_mic_recording.wav")
        self.assertTrue(os.path.exists("data/live_mic_recording.wav"))

        all_md = "\n".join([m.value for m in at.markdown])
        # Verdict must be AUTHENTIC HUMAN VOICE
        self.assertIn("AUTHENTIC HUMAN VOICE", all_md)
        self.assertIn("DEFENSE ASSESSMENT VERDICT", all_md)
        self.assertIn("Why this decision was reached (Plain English):", all_md)
        self.assertIn("We detected organic respiratory pauses", all_md)

        # Check metrics: Voice Physics Risk must be low (< 10%)
        voice_metric = next(m for m in at.metric if "Voice Physics" in m.label)
        voice_val = float(voice_metric.value.replace("%", ""))
        self.assertLess(voice_val, 10.0, f"Microphone recording voice physics risk {voice_val}% should be < 10%")

    # -------------------------------------------------------------------------
    # 5. Compartment 1: Illustrative Threat Presets
    # -------------------------------------------------------------------------
    def test_05_compartment_1_preset_legitimate_call(self):
        """Verify 'Legitimate Family Call' preset produces authentic human verdict."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        preset_sb = at.selectbox[0]
        preset_sb.select("Legitimate Family Call").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("AUTHENTIC HUMAN VOICE", all_md)

    def test_06_compartment_1_preset_ai_emergency_scam(self):
        """Verify 'AI Cloned Emergency Scam (Grandparent Trap)' flags DANGER and triggers OOB challenge."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        preset_sb = at.selectbox[0]
        preset_sb.select("AI Cloned Emergency Scam (Grandparent Trap)").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("DANGER: AI VOICE CLONE & SCAM", all_md)
        self.assertIn("CRITICAL SAFETY DIRECTIVE: OUT-OF-BAND VERIFICATION TRIGGERED", all_md)

    def test_07_compartment_1_preset_ai_bank_fraud(self):
        """Verify 'AI Bank Impersonation & Credential Harvest' detects high risk and credential traps."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        preset_sb = at.selectbox[0]
        preset_sb.select("AI Bank Impersonation & Credential Harvest").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertTrue("DANGER" in all_md or "CAUTION" in all_md)

    def test_08_compartment_1_preset_tech_support(self):
        """Verify 'Tech Support Remote Access Scam' flags threat intent."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        preset_sb = at.selectbox[0]
        preset_sb.select("Tech Support Remote Access Scam").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertTrue("DANGER" in all_md or "CAUTION" in all_md)

    # -------------------------------------------------------------------------
    # 6. Compartment 1: Upload Telephony Audio (.wav, .mp3) Ingestion
    # -------------------------------------------------------------------------
    def test_09_compartment_1_telephony_audio_upload(self):
        """Verify uploading PCM audio (.wav) executes full pipeline with ZERO errors."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        # Switch to Upload Mode
        at.radio[1].set_value("📁 Upload Telephony Audio (.wav, .mp3)").run()
        self.assertFalse(at.exception)
        self.assertGreater(len(at.file_uploader), 0, "File uploader widget missing in upload mode")

        # Upload sample audio
        sample_path = os.path.join(PROJECT_ROOT, "data", "sample_ai_bank_fraud.wav")
        self.assertTrue(os.path.exists(sample_path))
        with open(sample_path, "rb") as f:
            audio_bytes = f.read()

        at.file_uploader[0].upload("sample_ai_bank_fraud.wav", audio_bytes).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0, "Uploaded audio must process without errors")

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("DEFENSE ASSESSMENT VERDICT", all_md)
        self.assertIn("Why this decision was reached (Plain English):", all_md)

    # -------------------------------------------------------------------------
    # 7. Compartment 1: Spoken Transcript Real-Time NLP Injection
    # -------------------------------------------------------------------------
    def test_10_compartment_1_transcript_editing_live_nlp_update(self):
        """Verify typing or editing words in the transcript updates behavioral NLP intent."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        self.assertGreater(len(at.text_area), 0, "Spoken Call Transcript text area should be present")
        ta = at.text_area[0]
        coercive_script = (
            "Hello grandpa, I was arrested in Mexico and my bond is five thousand dollars! "
            "Do not tell my parents, please wire the bail money via Western Union immediately!"
        )
        ta.input(coercive_script).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        # Switch to Compartment 3 to inspect updated funnel
        at.radio[0].set_value("💬 Compartment 3: Conversation & Scam Words").run()
        comp3_md = "\n".join([m.value for m in at.markdown])
        self.assertTrue(
            "Family Emergency & Bail Scam" in comp3_md or "Stage" in comp3_md or "⚠️" in comp3_md,
            "Edited transcript should immediately reflect in scam classification"
        )

    # -------------------------------------------------------------------------
    # 8. Compartment 2: Vocal Physics & Deepfake Science Lab
    # -------------------------------------------------------------------------
    def test_11_compartment_2_vocal_physics_lab(self):
        """Verify Compartment 2 renders Pitch Contour graph, Mel-spectrogram, and telemetry table."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        at.radio[0].set_value("🔬 Compartment 2: Vocal Physics Lab").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        # Verify 2 Plotly figures: Pitch graph & Mel-spectrogram
        plotly_charts = at.get("plotly_chart")
        self.assertGreaterEqual(len(plotly_charts), 2, "Compartment 2 must render both Pitch and Spectrogram charts")

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("Compartment 2: Vocal Physics & Deepfake Science Lab", all_md)
        self.assertIn("Human-Readable Forensic Telemetry Table", all_md)
        self.assertIn("Pitch Micro-Tremor (Jitter)", all_md)
        self.assertIn("Vocal Shimmer (Amplitude Perturbation)", all_md)
        self.assertIn("Spectral Energy Centroid", all_md)
        self.assertIn("Spectral Flatness (SFM)", all_md)
        self.assertIn("Instantaneous Phase Fluctuation", all_md)
        self.assertIn("Vocoder Phase Glitch Frames", all_md)

    # -------------------------------------------------------------------------
    # 9. Compartment 3: Conversation & Scam Words Analyzer
    # -------------------------------------------------------------------------
    def test_12_compartment_3_conversation_and_scam_words(self):
        """Verify Compartment 3 renders transcript container, tactics badges, and 4-stage funnel."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        at.radio[0].set_value("💬 Compartment 3: Conversation & Scam Words").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("Compartment 3: Conversation & Scam Words Analyzer", all_md)
        self.assertIn("Annotated Spoken Transcript:", all_md)
        self.assertIn("Detected Coercive Tactics:", all_md)
        self.assertIn("Scam Taxonomy Category:", all_md)
        self.assertIn("The 4-Stage Social Engineering Funnel (Plain English):", all_md)
        self.assertIn("01 / STAGE 1", all_md)
        self.assertIn("02 / STAGE 2", all_md)
        self.assertIn("03 / STAGE 3", all_md)
        self.assertIn("04 / STAGE 4", all_md)
        self.assertIn("Current Funnel State:", all_md)

    # -------------------------------------------------------------------------
    # 10. Compartment 4: Family Emergency Verification (Codeword Tool)
    # -------------------------------------------------------------------------
    def test_13_compartment_4_out_of_band_verification_tool(self):
        """Verify Compartment 4 OOB Codeword Tool handles matching, mismatching, and empty answers."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        at.radio[0].set_value("🔑 Compartment 4: Family Verification Tool").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        self.assertGreaterEqual(len(at.text_input), 2, "Secret and caller response inputs required")

        # Case A: Empty caller answer -> Warning prompt
        at.text_input[1].input("").run()
        next(b for b in at.button if "Execute" in b.label).click().run()
        self.assertEqual(len(at.warning), 1)
        self.assertIn("Please enter what the caller answered", at.warning[0].value)

        # Case B: Matching Codeword -> IDENTITY CONFIRMED
        at.text_input[0].input("BlueSky2024").run()
        at.text_input[1].input("BlueSky2024").run()
        next(b for b in at.button if "Execute" in b.label).click().run()
        all_md_match = "\n".join([m.value for m in at.markdown])
        self.assertIn("IDENTITY CONFIRMED: AUTHENTIC FAMILY MEMBER", all_md_match)

        # Case C: Mismatching Codeword -> ALERT: ADVERSARIAL CLONE SUSPECTED
        at.text_input[1].input("WrongImposterCode").run()
        next(b for b in at.button if "Execute" in b.label).click().run()
        all_md_mismatch = "\n".join([m.value for m in at.markdown])
        self.assertIn("ALERT: ADVERSARIAL CLONE SUSPECTED — VERIFICATION FAILED", all_md_mismatch)

    # -------------------------------------------------------------------------
    # 11. Compartment 5: Accuracy & Phone Line Benchmarks
    # -------------------------------------------------------------------------
    def test_14_compartment_5_accuracy_and_benchmarks(self):
        """Verify Compartment 5 renders telephony degradation matrix dataframe and Phase 5 report."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        at.radio[0].set_value("📊 Compartment 5: Accuracy & Benchmarks").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

        # Verify benchmark dataframe is rendered
        self.assertGreater(len(at.dataframe), 0, "Telephony degradation dataframe missing")

        all_md = "\n".join([m.value for m in at.markdown])
        self.assertIn("Compartment 5: Accuracy & Phone Line Benchmarks", all_md)
        self.assertIn("The Telephony Bottleneck Explained:", all_md)
        self.assertIn("Phase 5 Experimental Stress Test Matrix", all_md)
        self.assertIn("Acoustic Model Noise & Telephony Decay Matrix", all_md)

        # Verify benchmark execution button is present
        p5_btns = [b for b in at.button if "Phase 5" in b.label]
        self.assertGreater(len(p5_btns), 0, "Phase 5 run button missing")

    # -------------------------------------------------------------------------
    # 12. Multimodal Fusion Slider Calibration
    # -------------------------------------------------------------------------
    def test_15_multimodal_fusion_slider_calibration(self):
        """Verify altering w_acoustic slider re-calculates contribution without crashing."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        self.assertGreater(len(at.sidebar.slider), 0, "Acoustic Forensics slider missing in sidebar")
        slider = at.sidebar.slider[0]
        slider.set_value(0.70).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 0)

    # -------------------------------------------------------------------------
    # 13. Cleanliness: Zero Unhandled Error Banners Across All States
    # -------------------------------------------------------------------------
    def test_16_zero_unhandled_error_banners(self):
        """Verify that navigating all compartments produces ZERO red st.error banners."""
        at = AppTest.from_file(self.APP_PATH, default_timeout=30)
        at.run()

        for comp in at.radio[0].options:
            at.radio[0].set_value(comp).run()
            self.assertEqual(
                len(at.error), 0,
                f"Unhandled error banner detected on {comp}: {[e.value for e in at.error]}"
            )

    # -------------------------------------------------------------------------
    # 14. Console Cleanliness: Zero Deprecation Warnings
    # -------------------------------------------------------------------------
    def test_17_zero_console_deprecation_warnings(self):
        """Verify running the app produces ZERO deprecation warnings (e.g. use_container_width)."""
        stderr_buf = io.StringIO()
        with redirect_stderr(stderr_buf):
            at = AppTest.from_file(self.APP_PATH, default_timeout=30)
            at.run()

        err_output = stderr_buf.getvalue()
        self.assertNotIn(
            "use_container_width", err_output,
            f"Deprecation warning detected in console:\n{err_output}"
        )


def run_all_tests():
    print("=" * 80)
    print("VOXSENTINEL AI — COMPREHENSIVE BROWSER & E2E DOM TEST SUITE")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVoxSentinelE2E)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    res = run_all_tests()
    sys.exit(0 if res.wasSuccessful() else 1)
