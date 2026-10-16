import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import unittest
from src.data.prepare_content_dataset import prepare_content_dataset
from src.nlp.train_content_classifier import train_content_classifier
from src.nlp.content_engine import ContentEngine

class TestPhase3ContentEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_path = "data/phase3/content_dataset.csv"
        cls.df = prepare_content_dataset(output_path=cls.dataset_path)
        cls.engine = ContentEngine(model_dir="models")

    def test_dataset_generation(self):
        self.assertTrue(os.path.exists(self.dataset_path))
        self.assertGreater(len(self.df), 100)

    def test_content_classifier_training(self):
        results = train_content_classifier(data_path=self.dataset_path, model_dir="models")
        self.assertIn("accuracy", results)
        self.assertGreaterEqual(results["accuracy"], 0.85)

    def test_scam_text_classification(self):
        scam_text = "Grandma please help me! I got into a car crash and need $5,000 wire transfer for bail immediately!"
        res = self.engine.analyze_text(scam_text)
        self.assertGreaterEqual(res["scam_probability"], 0.5)
        self.assertTrue(res["is_scam"])
        self.assertIn("Family Emergency & Bail Scam", res["category"])
        self.assertIn("wire transfer", res["flagged_phrases"])

    def test_normal_text_classification(self):
        normal_text = "Hi Mom, just checking in to see if we are still meeting for dinner on Saturday at 7 PM?"
        res = self.engine.analyze_text(normal_text)
        self.assertLess(res["scam_probability"], 0.5)
        self.assertFalse(res["is_scam"])

if __name__ == "__main__":
    unittest.main()
