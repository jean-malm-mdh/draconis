import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from reqcheck import complies


# Todo:
class ComplianceCheckGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_generate_basic_warning(self):
        req_text = "the number of variables should be above 50"
        metrics = {"variable": 55}
        self.assertTrue(complies(metrics, req_text), "Positive test")
        metrics = {"variable": 45}
        self.assertFalse(complies(metrics, req_text), "negative test")
        metrics = {"variable": 50}
        self.assertFalse(complies(metrics, req_text), "Boundary value - 50 != above 50")
        metrics = {"variable": 51}
        self.assertTrue(complies(metrics, req_text), "Boundary value - 51 is above 50")

    def test_can_handle_negation(self):
        req_text = "the number of variables should not be above 50"
        metrics = {"variable": 55}
        self.assertFalse(complies(metrics, req_text))

    def test_can_handle_interval(self):
        req_text = "the number of variables should be between 55 and 125"
        metrics = {"variable": 55}
        self.assertTrue(complies(metrics, req_text), "positive test")
        metrics = {"variable": 125}
        self.assertTrue(complies(metrics, req_text), "positive test - upper boundary value")
        metrics = {"variable": 0}
        self.assertFalse(complies(metrics, req_text), "negative test")
        metrics = {"variable": 126}
        self.assertFalse(complies(metrics, req_text), "negative test - upper boundary")

    def test_can_handle_compound_metrics(self):
        req_text = "the total number of in- and output variables shall not exceed 5"
        metrics = {"inputVariable": 2, "outputVariable": 1}
        self.assertTrue(complies(metrics, req_text), "Positive test")

if __name__ == '__main__':
    unittest.main()
