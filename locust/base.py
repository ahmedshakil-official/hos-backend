import random
import string

from locust import HttpUser, between

from config import CREDENTIALS


class BaseWebTasks(HttpUser):
    abstract = True
    wait_time = between(1, 2)

    def get_keyword(
        self,
    ):
        """Generate a random string of random length"""
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(random.randint(2, 5)))

    # login with credentials
    def on_start(self):
        response = self.client.post(
            "/api/v1/token/",
            json=dict(id=CREDENTIALS["PHONE"], password=CREDENTIALS["PASSWORD"]),
        )
        if response.status_code != 200:
            raise ValueError
        data = response.json()
        self.token = data.get("access")
        self.headers = dict(Authorization=f"Bearer {self.token}")
        self.post_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
