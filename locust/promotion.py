from locust import task
from base import BaseWebTasks

from payloads import promotion_payload


class PromotionTasks(BaseWebTasks):

    # @task
    # def promotion_popup_message_published_post(self):
    #     url = "/api/v1/promotion/popup/messages/published/"
    #     response = self.client.post(
    #         url,
    #         name="published-popup-message-list",
    #         headers=self.post_headers,
    #         json=promotion_payload.popup_message_published_payload
    #     )
    #
    #     assert response.status_code == 201

    @task
    def promotion_popup_message_published_list(self):
        url = "/api/v1/promotion/popup/messages/published/"
        response = self.client.get(
            url,
            name="published-popup-message-list",
            headers=self.headers,
        )
