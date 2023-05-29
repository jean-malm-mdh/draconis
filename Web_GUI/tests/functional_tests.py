from selenium import webdriver
import pytest


def test_basic_functional():
    browser = webdriver.Firefox()
    browser.get("http://localhost:8000")

    assert "install worked" in browser.title.lower()
