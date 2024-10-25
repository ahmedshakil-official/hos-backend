from locust import task
from base import BaseWebTasks

class LighthouseTasks(BaseWebTasks):
    @task
    def get_ecommerce_wishlist_items_stocks(self):
        url = "/api/v1/ecommerce/wishlist-items/stocks/"
        name = url
        self.client.get(url, name=name, headers=self.headers)

    @task
    def get_organization_employee_permission_group(self):
        url = "/api/v1/users/organizations/permission-group/employee/"
        name = url
        self.client.get(url, name=name, headers=self.headers)

    @task
    def get_short_return_item_wise(self):
        url = "/api/v1/ecommerce/short-return/item-wise/"
        name = url
        self.client.get(url, name=name, headers=self.headers)

    @task
    def get_short_return_details(self):
        url = "/api/v1/ecommerce/shorts/"
        name = url
        response = self.client.get(url, name=name, headers=self.headers)
        json_data = response.json()
        alias = None

        if "results" in json_data and json_data["results"]:
            alias = json_data["results"][0].get("alias")

        url = f"/api/v1/ecommerce/short-return/{alias}/"
        name = url

        self.client.get(url, name=name, headers=self.headers)
