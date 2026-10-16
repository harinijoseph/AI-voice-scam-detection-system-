import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import unittest
import numpy as np
from src.data.dataset_loader import prepare_phase1_dataset
from src.audio.feature_extractor import extract_acoustic_features
from src.audio.train_acoustic_rf import run_phase1_baseline

class TestPhase1AcousticBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reals, cls.fakes = prepare_phase1_dataset(num_clips_per_class=10)

    def test_dataset_generation(self):
        self.assertEqual(len(self.reals), 10)
        self.assertEqual(len(self.fakes), 10)
        for f in self.reals + self.fakes:
            self.assertTrue(os.path.exists(f))

    def test_feature_extractor_dimensions(self):
        sample_file = self.reals[0]
        import librosa
        y, sr = librosa.load(sample_file, sr=16000)
        vec, names = extract_acoustic_features(y, sr)
        
        self.assertEqual(len(vec), 400) # DeepGuard Features: MFCC (80) + Delta MFCC (40) + Mel-Spec (256) + Chroma (12) + Contrast (7) + ZCR (2) + RMS (2) + Rolloff (1)
        self.assertEqual(len(vec), len(names))
        self.assertFalse(np.isnan(vec).any())

    def test_phase1_pipeline_execution(self):
        metrics = run_phase1_baseline()
        self.assertIn("accuracy", metrics)
        self.assertIn("eer", metrics)
        self.assertGreaterEqual(metrics["accuracy"], 0.80)

if __name__ == "__main__":
    unittest.main()
