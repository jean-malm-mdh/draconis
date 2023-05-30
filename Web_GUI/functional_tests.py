from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import unittest

class NewVisitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.browser = webdriver.Firefox()
    def tearDown(self) -> None:
        self.browser.quit()

    def test_can_view_basic_report(self):
        self.browser.get("http://localhost:8000")

        self.assertIn("Report Findings", self.browser.title)
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Reports", header_text)
        table = self.browser.find_element(By.ID, value="id_reports_table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        self.assertIsNot(list(rows), [])

if __name__ == "__main__":
    unittest.main()