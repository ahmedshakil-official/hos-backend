import os
import dotenv

current_directory = os.getcwd()
dotenv_path = f"{current_directory}/projectile/.env"

dotenv.read_dotenv(dotenv_path)

# Keep test user info / credentials here
phone = os.getenv("LOCUST_USER_ID", default=None)
password = os.getenv("LOCUST_USER_PASSWORD", default=None)

CREDENTIALS = {
    "PHONE": phone,
    "PASSWORD": password
}

# The global params to control the requests
REQUEST_PARAMS = {
    'min_wait': 200,
    'max_wait': 5000
}
