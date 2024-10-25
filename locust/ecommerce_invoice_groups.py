from locust import task
from base import BaseWebTasks

from payloads import invoice_group_payload


class EcommerceInvoiceGroupTask(BaseWebTasks):
    @task
    def ecommerce_order_invoice_group(self):
        url = "/api/v1/ecommerce/invoice-groups/"
        order_invoice_group_response = self.client.get(
            url, name="invoice-group-list", headers=self.headers
        )
        self.order_invoice_group_response = order_invoice_group_response

    @task
    def ecommerce_order_invoice_group_post(self):
        url = "/api/v1/ecommerce/invoice-groups/"
        order_invoice_group_post_response = self.client.post(
            url,
            name="invoice-group-list",
            headers=self.headers,
            json=invoice_group_payload.order_invoice_group_payload,
        )

    @task
    def ecommerce_order_invoice_group_details(self):
        json_data = self.order_invoice_group_response.json()
        if "results" in json_data and json_data["results"]:
            alias: str = json_data["results"][0].get("alias")
            url = f"/api/v1/ecommerce/invoice-groups/{alias}/"
            response = self.client.get(
                url, name="invoice-group-details", headers=self.headers
            )

    @task
    def ecommerce_invoice_group_delivery_sheet(self):
        url = "/api/v1/ecommerce/invoice-group/delivery-sheets/"
        invoice_group_delivery_sheet_response = self.client.get(
            url, name="invoice-group-delivery-sheet-list", headers=self.headers
        )

    @task
    def responsible_employee_wise_invoice_group_delivery_sheet(self):
        url = "/api/v1/ecommerce/invoice-group/delivery-sheet/"
        response = self.client.get(
            url, name="invoice-group-delivery-sheet-list", headers=self.headers
        )

    @task
    def short_return_log_item_wise_list(self):
        url = "/api/v1/ecommerce/short-return/item-wise/"

        response = self.client.get(
            url, name="short-return-list-item-wise", headers=self.headers
        )
