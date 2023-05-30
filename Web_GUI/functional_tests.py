import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import unittest

class NewVisitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.browser = webdriver.Firefox()
    def tearDown(self) -> None:
        self.browser.quit()

    def test_can_view_and_edit_basic_report(self):
        self.browser.get("http://localhost:8000")

        self.assertIn("Report Findings", self.browser.title)
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Reports", header_text)
        table = self.browser.find_element(By.ID, value="id_reports_table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        self.assertIsNot(list(rows), [])
        ROW_TO_SELECT = -1
        time.sleep(2)
        # Select the last report to add review comment
        table.find_elements(By.NAME, "selected")[ROW_TO_SELECT].click()
        time.sleep(1)

        # Write the review
        review_textbox = self.browser.find_element(By.ID, "review_comment")
        review_textbox.send_keys("This is my amended review comment for the issue")
        time.sleep(2)
        #Send the review
        review_textbox.send_keys(Keys.ENTER)

        time.sleep(1)
        affected_review = self.browser.find_element(By.ID, "rev2")

        self.assertIn("This is my amended review comment for the issue",
                      affected_review.text)

if __name__ == "__main__":
    unittest.main()