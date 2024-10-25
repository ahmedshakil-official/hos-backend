import contextlib

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.utils import track_execute_time

from ..test_case import BaseSeleniumTestCase
from ..config import CONFIG


class LoginTestCase(BaseSeleniumTestCase):

    @track_execute_time()
    def test_login(self):
        driver = self.driver
        # open the link we want to test
        driver.get(CONFIG["BASE_URL"])

        # try login with CONFIG user credential
        # Find and fill in the email/phone number field
        email_phone_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]'))
        )
        email_phone_field.send_keys(CONFIG.get("USERNAME"))

        # Find and fill in the password field
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
        )
        password_field.send_keys(CONFIG.get("PASSWORD"))

        # Find and click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[style*="background-color: rgb(70, 215, 182)"]'))
        )
        login_button.click()
        timeout=10
        # Our home page title is Home, if driver is in home means we successfully logged in
        # Wait for the title to be present
        with contextlib.suppress(Exception):
            WebDriverWait(driver, timeout).until(EC.title_is("Home"))

        assert "Home" == driver.title
