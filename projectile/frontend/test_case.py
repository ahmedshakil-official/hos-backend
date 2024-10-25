import os

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from .config import CONFIG


class BaseSeleniumTestCase(LiveServerTestCase):
    """
    Base test case for selenium automation testing of the frontend
    using LiveServerTestCase to run the automation as like Django unit test

    NOTE: make sure we have driver on the same level as this file.
    driver path level:
        test_case.py
        drivers/chromedriver
    """
    driver = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drivers', CONFIG['DRIVER'])
    service = Service(executable_path=driver)

    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run Chrome in headless mode
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

        super(BaseSeleniumTestCase, self).setUp()

    def tearDown(self):
        self.driver.quit()
        super(BaseSeleniumTestCase, self).tearDown()
