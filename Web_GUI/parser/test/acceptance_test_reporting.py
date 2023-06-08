import unittest

from Web_GUI.parser.helper_functions import parse_pou_file


class FBDParseReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.programs = dict([(n, parse_pou_file(p)) for n, p in
                     [("Calc_Odd", "Collatz_Calculator_Odd.pou"),
                      ("Calc_Even", "Collatz_Calculator_Even.pou"),
                      ("Calc_Even_SafeVer", "Collatz_Calculator_Even_UnsafeIn_SafeOut.pou"),
                      ("MultiAND", "MultiANDer.pou"),
                      ("SingleIn_MultiOut", "TestPOU_SingleInput_MultipleOutput.pou"),
                      ("output_has_non_outputs", "output_has_non_output_vars.pou"),
                      ("input_has_non_inputs", "input_has_non_input_vars.pou"),
                      ("empty_no_proper_groups", "empty_prog_no_groups.pou")
                      ]])

    def test_report_text_includes_variable_numeric_metrics(self):
        """Code-REQ-028"""
        prog_report_1 = self.programs["Calc_Odd"].report_as_text()

        self.assertIn("Metrics", prog_report_1)
        self.assertIn("Num_Inputs: 1", prog_report_1)
        self.assertIn("Num_Outputs: 1", prog_report_1)

        prog_report_2 = self.programs["MultiAND"].report_as_text()
        self.assertIn("Num_Inputs: 3", prog_report_2)
        self.assertIn("Num_Outputs: 1", prog_report_2)

        prog_report_3 = self.programs["SingleIn_MultiOut"].report_as_text()
        self.assertIn("Num_Inputs: 1", prog_report_3)
        self.assertIn("Num_Outputs: 2", prog_report_3)

    def test_report_text_includes_variable_names_and_comments(self):
        """Code-REQ-021 -- 022"""
        prog_report_1 = self.programs["Calc_Odd"].report_as_text()
        self.assertIn("Variables", prog_report_1)


if __name__ == '__main__':
    unittest.main()
