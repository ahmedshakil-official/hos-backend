import os

CONFIG = {
    "BASE_URL": os.getenv("SITE_LINK", None),
    'USERNAME': os.getenv("SELENIUM_USER_ID", None),
    'PASSWORD': os.getenv("SELENIUM_USER_PASSWORD", None),
    'DRIVER': 'chromedriver',
}
