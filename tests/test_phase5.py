import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import unittest
from src.eval.run_phase5_experiments import run_phase5_robustness_experiments

class TestPhase5RobustnessAndGeneralization(unittest.TestCase):
    def test_phase5_experiments_run(self):
        report_path = "data/phase5/test_robustness_report.md"
        results = run_phase5_robustness_experiments(output_report_path=report_path)
        
        self.assertTrue(os.path.exists(report_path))
        self.assertIn("res_clean", results)
        self.assertIn("res_snr10", results)
        self.assertIn("res_telephony", results)
        self.assertIn("res_unseen_generator", results)
        self.assertGreaterEqual(results["content_unseen_acc"], 0.75)

if __name__ == "__main__":
    unittest.main()
