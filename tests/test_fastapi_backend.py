"""
VoxSentinel AI — FastAPI Backend End-to-End Test Suite
Tests all REST API routes: health, presets, audio streaming, audio analysis,
codeword verification, and empirical benchmarks.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app

class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("monitoring_active"), True)
        self.assertIn("device", data)

    def test_02_presets_endpoint(self):
        resp = self.client.get("/api/presets")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("presets", data)
        presets = data["presets"]
        self.assertEqual(len(presets), 4)
        
        # Verify preset IDs exist
        preset_ids = [p["id"] for p in presets]
        self.assertIn("legitimate_family_call", preset_ids)
        self.assertIn("ai_grandparent_scam", preset_ids)
        self.assertIn("ai_bank_fraud", preset_ids)
        self.assertIn("ai_tech_support", preset_ids)

    def test_03_preset_audio_streaming(self):
        resp = self.client.get("/api/presets/legitimate_family_call/audio")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("audio/wav", resp.headers.get("content-type", ""))
        self.assertGreater(len(resp.content), 1000)

    def test_04_verification_codeword_match(self):
        payload = {
            "secret_codeword": "BlueSky2024",
            "caller_response": "BlueSky2024"
        }
        resp = self.client.post("/api/verify/codeword", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("verified"))
        self.assertEqual(data.get("status"), "CONFIRMED")
        self.assertIn("IDENTITY CONFIRMED", data.get("title", ""))

    def test_05_verification_codeword_mismatch(self):
        payload = {
            "secret_codeword": "BlueSky2024",
            "caller_response": "WrongImposterCode"
        }
        resp = self.client.post("/api/verify/codeword", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get("verified"))
        self.assertEqual(data.get("status"), "FAILED")
        self.assertIn("ALERT: ADVERSARIAL CLONE SUSPECTED", data.get("title", ""))

    def test_06_verification_codeword_empty(self):
        payload = {
            "secret_codeword": "BlueSky2024",
            "caller_response": ""
        }
        resp = self.client.post("/api/verify/codeword", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get("verified"))
        self.assertEqual(data.get("status"), "AWAITING_INPUT")

    def test_07_verification_questions_library(self):
        resp = self.client.get("/api/verify/questions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("questions", data)
        self.assertGreaterEqual(len(data["questions"]), 4)

    def test_08_benchmarks_matrix(self):
        resp = self.client.get("/api/benchmarks/matrix")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("matrix", data)
        self.assertEqual(len(data["matrix"]), 6)

    def test_09_analyze_audio_live_mic(self):
        mic_path = os.path.join(PROJECT_ROOT, "data", "live_mic_recording.wav")
        if not os.path.exists(mic_path):
            self.skipTest("data/live_mic_recording.wav not found")

        with open(mic_path, "rb") as f:
            resp = self.client.post(
                "/api/analyze/audio",
                files={"audio_file": ("live_mic_recording.wav", f, "audio/wav")},
                data={"transcript": "hello this is my real voice", "w_acoustic": "0.5", "is_microphone": "true"}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("verdict", data)
        # Should classify real human voice as authentic safe
        self.assertIn("AUTHENTIC HUMAN VOICE", data["verdict"].get("title", ""))
        self.assertLess(data.get("overall_risk_score", 1.0), 0.35)
        self.assertGreater(len(data.get("telemetry_rows", [])), 0)
        self.assertGreater(len(data.get("pitch_points", [])), 0)

    def test_10_analyze_audio_scam(self):
        scam_path = os.path.join(PROJECT_ROOT, "data", "sample_ai_grandparent_scam.wav")
        if not os.path.exists(scam_path):
            self.skipTest("data/sample_ai_grandparent_scam.wav not found")

        with open(scam_path, "rb") as f:
            resp = self.client.post(
                "/api/analyze/audio",
                files={"audio_file": ("sample_ai_grandparent_scam.wav", f, "audio/wav")},
                data={
                    "transcript": "Grandma please help me! Wire 5000 dollars cash bail immediately!",
                    "w_acoustic": "0.5",
                    "is_microphone": "false"
                }
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("DANGER: AI VOICE CLONE & SCAM", data["verdict"].get("title", ""))
        self.assertGreaterEqual(data.get("overall_risk_score", 0.0), 0.65)

    def test_11_analyze_audio_empty_file_fails(self):
        resp = self.client.post(
            "/api/analyze/audio",
            files={"audio_file": ("empty.wav", b"", "audio/wav")},
            data={"w_acoustic": "0.5"}
        )
        self.assertEqual(resp.status_code, 400)

    def test_12_react_frontend_mounted(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("content-type", ""))
        self.assertIn("root", resp.text)

    def test_13_dataset_stats(self):
        resp = self.client.get("/api/benchmarks/dataset/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("total_files"), 2088)
        self.assertEqual(data["categories"]["human"]["count"], 1001)
        self.assertEqual(data["categories"]["nonhuman"]["count"], 1000)
        self.assertEqual(data["categories"]["possible"]["count"], 87)
        self.assertTrue(data.get("ready"))

    def test_14_dataset_samples_listing(self):
        resp = self.client.get("/api/benchmarks/dataset/samples?category=human&limit=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("samples", data)
        self.assertEqual(len(data["samples"]), 5)
        sample = data["samples"][0]
        self.assertEqual(sample["category"], "human")
        self.assertIn(".mp3", sample["filename"])
        self.assertIn("/api/benchmarks/dataset/audio/human/", sample["audio_url"])

    def test_15_dataset_audio_streaming(self):
        # Fetch one sample first
        samples_resp = self.client.get("/api/benchmarks/dataset/samples?category=human&limit=1")
        sample_filename = samples_resp.json()["samples"][0]["filename"]

        resp = self.client.get(f"/api/benchmarks/dataset/audio/human/{sample_filename}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("audio/mpeg", resp.headers.get("content-type", ""))
        self.assertGreater(len(resp.content), 1000)

    def test_16_dataset_random_preset(self):
        resp = self.client.get("/api/presets/dataset-random?category=human")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["category"], "human")
        self.assertEqual(data["threat_level"], "safe")
        self.assertIn(".mp3", data["filename"])

        resp2 = self.client.get("/api/presets/dataset-random?category=nonhuman")
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["category"], "nonhuman")
        self.assertEqual(data2["threat_level"], "danger")

    def test_17_dataset_direct_analyze(self):
        samples_resp = self.client.get("/api/benchmarks/dataset/samples?category=human&limit=1")
        sample_filename = samples_resp.json()["samples"][0]["filename"]

        payload = {
            "category": "human",
            "filename": sample_filename,
            "w_acoustic": 0.50
        }
        resp = self.client.post("/api/analyze/dataset-sample", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("verdict", data)
        self.assertIn("dataset_metadata", data)
        self.assertEqual(data["dataset_metadata"]["category"], "human")
        self.assertGreater(len(data["telemetry_rows"]), 0)

    def test_18_dataset_batch_evaluation(self):
        payload = {
            "sample_size": 4
        }
        resp = self.client.post("/api/benchmarks/dataset/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_evaluated"], 4)
        self.assertIn("metrics", data)
        self.assertIn("confusion_matrix", data)
        self.assertIn("accuracy", data["metrics"])
        self.assertEqual(len(data["sample_results"]), 4)

    def test_19_dataset_stress_test(self):
        payload = {
            "samples_per_condition": 2
        }
        resp = self.client.post("/api/benchmarks/dataset/stress-test", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("dataset_tested"), "human-nonhuman")
        self.assertIn("stress_matrix", data)


if __name__ == "__main__":
    unittest.main()

