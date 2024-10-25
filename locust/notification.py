from locust import task
from base import BaseWebTasks


class NotificationTasks(BaseWebTasks):

    @task
    def notification_count_list(self):
        url = "/api/v1/notification/count/"
        response = self.client.get(
            url,
            name="user-notification-count",
            headers=self.headers
        )
