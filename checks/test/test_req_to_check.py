import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from reqcheck import classify, complies


# Todo:


class CheckClassifier(unittest.TestCase):

    def setUp(self) -> None:
        self.maxDiff = None

    def test_metric_basic(self):
        req_text = "the number of variables should be above 50"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "warning",
                              "target_function": ">",
                              "val": "50"},
                             classify(req_text))

    def test_metric_basic_below(self):
        req_text = "the number of variables should be below 50"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "warning",
                              "target_function": "<",
                              "val": "50"},
                             classify(req_text))

    def test_metrics_variable_example(self):
        req_text = "the number of variables shall not exceed 10"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "<=",
                              "val": "10"},
                             classify(req_text))

    def test_metrics_input_signal_numeric_value(self):
        req_text = "the number of variables shall not exceed 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "<=",
                              "val": "20"},
                             classify(req_text))

    def test_metrics_input_signal_numeric_value_as_text(self):
        req_text = "the number of variables shall not exceed fifteen"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "<=",
                              "val": "15"},
                             classify(req_text))

    def test_metrics_interval(self):
        req_text = "the number of variables shall be between 5 and 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

    def test_metrics_interval_lower_first(self):
        req_text = "the number of variables shall be between 20 and 5"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

    def test_metrics_interval_negative_number(self):
        req_text = "the number of variables shall be between -55 and 125"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "error",
                              "target_function": "interval",
                              "val": "[-55,125]"},
                             classify(req_text))

    def test_issue_level_warning(self):
        req_text = "the number of variables should be between 5 and 20"
        self.assertDictEqual({"check_type": "metric",
                              "property": "variable",
                              "issue_level": "warning",
                              "target_function": "interval",
                              "val": "[5,20]"},
                             classify(req_text))

    def test_non_atomic_property(self):
        req_text = "the total number of in- and output variables shall not exceed 5"
        self.assertDictEqual({"check_type": "metric",
                              "property": "SUM([input_variable,output_variable])",
                              "issue_level": "error",
                              "target_function": "<=",
                              "val": "5"},
                             classify(req_text))


if __name__ == '__main__':
    unittest.main()
