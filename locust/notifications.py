from locust import task
from base import BaseWebTasks

from payloads import notification_payload


class NotificationTask(BaseWebTasks):
    @task
    def notification_list(self):
        url = "/api/v1/notification/notifications-list-create/"
        response = self.client.get(
            url, name="list-create-notification", headers=self.headers
        )

    # @task
    # def notification_post(self):
    #     url = "/api/v1/notification/notifications-list-create/"
    #     response = self.client.post(
    #         url,
    #         name="list-create-notification",
    #         headers=self.headers,
    #         json=notification_payload.notification_post_payload,
    #     )
