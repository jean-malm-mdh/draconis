import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from reqcheck import classify

# Todo:

class MyTestCase(unittest.TestCase):
    def test_metrics_input_signal_example(self):
        req_text = "the number of variables shall not exceed 10"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_func": "not(>)",
                              "val": "10"},
                             classify(req_text))

    def test_metrics_input_signal_example2(self):
        req_text = "the number of variables shall not exceed 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_func": "not(>)",
                              "val": "20"},
                             classify(req_text))

    def test_metrics_interval(self):
        req_text = "the number of variables shall be between 5 and 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_func": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

    def test_metrics_interval_lower_first(self):
        req_text = "the number of variables shall be between 20 and 5"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_func": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

    def test_issue_level_warning(self):
        req_text = "the number of variables should be between 5 and 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "warning",
                              "target_func": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

if __name__ == '__main__':
    unittest.main()
