import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import unittest
import numpy as np
import librosa

from src.data.dataset_loader import prepare_phase1_dataset
from src.audio.acoustic_visualizer import generate_acoustic_visuals, plot_pitch_contour, plot_mel_spectrogram_with_anomalies

class TestPhase2AcousticVisualizations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reals, cls.fakes = prepare_phase1_dataset(num_clips_per_class=2)

    def test_pitch_contour_plot(self):
        sample_file = self.reals[0]
        y, sr = librosa.load(sample_file, sr=22050)
        fig, metrics = plot_pitch_contour(y, sr)
        
        self.assertIsNotNone(fig)
        self.assertIn("f0_mean", metrics)
        self.assertIn("f0_std", metrics)

    def test_mel_spectrogram_plot(self):
        sample_file = self.fakes[0]
        y, sr = librosa.load(sample_file, sr=22050)
        fig, metrics = plot_mel_spectrogram_with_anomalies(y, sr)
        
        self.assertIsNotNone(fig)
        self.assertIn("anomaly_frame_count", metrics)
        self.assertIn("total_frames", metrics)

    def test_generate_acoustic_visuals_pipeline(self):
        visuals = generate_acoustic_visuals(self.reals[0])
        self.assertIn("pitch_fig", visuals)
        self.assertIn("spectrogram_fig", visuals)
        self.assertIn("pitch_metrics", visuals)
        self.assertIn("spectrogram_metrics", visuals)

if __name__ == "__main__":
    unittest.main()
