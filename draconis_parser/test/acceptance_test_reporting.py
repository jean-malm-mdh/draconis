import unittest

from draconis_parser import (
    parse_pou_file,
    get_pou_description,
    change_pou_description,
    append_analysis_to_text,
)


class FBDParseReportTest(unittest.TestCase):
    descriptions = None
    programs = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.programs = dict(
            [
                (n, parse_pou_file(p))
                for n, p in [
                ("Calc_Odd", "Collatz_Calculator_Odd/Collatz_Calculator_Odd.pou"),
                (
                    "Calc_Even",
                    "Collatz_Calculator_Even/Collatz_Calculator_Even.pou",
                ),
                (
                    "Calc_Even_SafeVer",
                    "Collatz_Calculator_Even/Collatz_Calculator_Even_UnsafeIn_SafeOut.pou",
                ),
                ("MultiAND", "MultiANDer.pou"),
                ("SingleIn_MultiOut", "TestPOU_SingleInput_MultipleOutput.pou"),
                ("output_has_non_outputs", "output_has_non_output_vars.pou"),
                ("input_has_non_inputs", "input_has_non_input_vars.pou"),
                ("empty_no_proper_groups", "empty_prog_no_groups.pou"),
            ]
            ]
        )
        cls.descriptions = dict(
            [
                (n, (p, get_pou_description(p)))
                for n, p in [
                (
                    "Calc_Odd",
                    "Collatz_Calculator_Odd/DESCRIPTIONTranslation_SF.xml",
                ),
                (
                    "Calc_Even",
                    "Collatz_Calculator_Even/DESCRIPTIONTranslation_SF.xml",
                ),
            ]
            ]
        )

    @classmethod
    def tearDownClass(cls) -> None:
        for p, desc in cls.descriptions.values():
            change_pou_description(p, desc)

    def test_report_text_includes_variable_numeric_metrics(self):
        """Code-REQ-028"""
        prog_report_1 = FBDParseReportTest.programs["Calc_Odd"].report_as_text()

        self.assertIn("Metrics", prog_report_1)
        self.assertIn("Num_Inputs: 1", prog_report_1)
        self.assertIn("Num_Outputs: 1", prog_report_1)

        prog_report_2 = FBDParseReportTest.programs["MultiAND"].report_as_text()
        self.assertIn("Num_Inputs: 3", prog_report_2)
        self.assertIn("Num_Outputs: 1", prog_report_2)

        prog_report_3 = FBDParseReportTest.programs[
            "SingleIn_MultiOut"
        ].report_as_text()
        self.assertIn("Num_Inputs: 1", prog_report_3)
        self.assertIn("Num_Outputs: 2", prog_report_3)

    def test_report_text_includes_variable_names_and_comments(self):
        """Code-REQ-021 -- 022"""
        prog_report_1 = FBDParseReportTest.programs["Calc_Odd"].report_as_text()
        prog_report_2 = FBDParseReportTest.programs["MultiAND"].report_as_text()
        self.assertIn("Variables", prog_report_1)
        self.assertIn("Variables", prog_report_2)
        # Check inputs
        self.assertIn("(N, InputVar, UINT, 1, Collatz Input)", prog_report_1)
        self.assertIn(
            "(IsOn_ST, InputVar, SAFEBOOL, UNINIT, If system is on)", prog_report_2
        )

        # Check Outputs
        self.assertIn(
            "(Result_Odd, OutputVar, UINT, 0, Result if the input is an odd number)",
            prog_report_1,
        )
        self.assertIn(
            "(CanDoWork_ST, OutputVar, SAFEBOOL, UNINIT, If System can do work)",
            prog_report_2,
        )

    def test_can_retrieve_pou_description_from_file(self):
        original_description_content = get_pou_description(
            "DESCRIPTIONTranslation_SF.xml"
        )
        self.assertEqual(original_description_content, "Do_Not_Change_this")

    def test_can_change_pou_description_in_file(self):
        test_file = "DESCRIPTIONTranslation_SF.xml"
        original_description_content = get_pou_description(test_file)
        change_string = "OK! You changed this"
        change_pou_description(test_file, change_string)
        self.assertEqual(get_pou_description(test_file), change_string)
        # check that reset has gone through
        change_pou_description(test_file, original_description_content)
        self.assertNotEqual(get_pou_description(test_file), change_string)

    def test_can_output_to_description_file_show_then_clean_up(self):
        # The selected program is analysed, and a report is generated
        prog_report = parse_pou_file(
            "Collatz_Calculator_Odd/Collatz_Calculator_Odd.pou"
        ).report_as_text()

        # The current description is read
        pou_description_file = "Collatz_Calculator_Odd/DESCRIPTIONTranslation_SF.xml"
        original_description_content = get_pou_description(pou_description_file)

        # Append report info to description
        description_with_report = append_analysis_to_text(
            original_description_content, prog_report
        )

        # Update the POU Description
        change_pou_description(pou_description_file, description_with_report)

        # Assert that update has been made, and report info is in the file
        new_description_content = get_pou_description(pou_description_file)
        self.assertIn("Metrics", new_description_content)
        self.assertIn("Variables", new_description_content)

        # Reset things
        change_pou_description(pou_description_file, original_description_content)


if __name__ == "__main__":
    unittest.main()
