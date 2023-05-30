from django.test import TestCase
from django.urls import resolve
import sys
import os
sys.path.extend(os.path.dirname(__file__))
from reports.views import home_page
# Create your tests here.
class HomepageTest(TestCase):

    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")
        self.assertEqual(found.func, home_page)