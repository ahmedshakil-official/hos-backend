from rest_framework import status

from locust import task
from base import BaseWebTasks

from payloads import distributor_payload as payload


class DistributorTasks(BaseWebTasks):
    stock_alias = ""

    @task
    def distributor_order(self):
        url = "/api/v1/pharmacy/distributor/order/"
        distributor_order_response = self.client.get(
            url, name="distributor-order-list-create", headers=self.headers
        )
        self.distributor_order_response = distributor_order_response

    @task
    def distributor_stock_products(self):
        stock_product_url = "/api/v1/pharmacy/distributor/stocks/products/"
        stock_product_response = self.client.get(
            stock_product_url,
            name="pharmacy.distributor-sales-able-stock-product.list",
            headers=self.headers,
        )
        self.stock_product_response = stock_product_response

    @task
    def distributor_cart(self):
        url = "/api/v1/pharmacy/distributor/order/cart/"
        self.client.get(
            url, name="distributor-order-cart-list-create", headers=self.headers
        )

    @task
    def distributor_product_order_limit(self):
        self.stock_alias = None
        stock_alias = None

        stock_product_url = "/api/v1/search/pharmacy/stock/products/e-com/"
        stock_product_response = self.client.get(
            stock_product_url, name="ecom_product_search_es", headers=self.headers
        )

        json_data = stock_product_response.json()
        if "results" in json_data and json_data["results"]:
            stock_alias = json_data["results"][0].get("alias")
        if stock_alias:
            self.stock_alias = stock_alias

        url = f"/api/v1/pharmacy/distributor/product/order-limit/{self.stock_alias}/"
        self.client.get(url, name="distributor-order-re-order", headers=self.headers)

    # It stores in db
    # @task
    # def distributor_order_cart_post(self):
    #     url = "/api/v1/pharmacy/distributor/order/cart/"
    #     cart_post_response = self.client.post(
    #         url,
    #         name="distributor-order-cart-list-create",
    #         headers=self.post_headers,
    #         json=payload.order_cart_payload,
    #     )
    #     assert cart_post_response.status_code == 201

    @task
    def distributor_product_reorder(self):
        url = "/api/v1/pharmacy/distributor/order/reorder/"
        self.client.get(url, name="distributor-order-re-order", headers=self.headers)

    @task
    def distributor_stock_products_flash(self):
        url = "/api/v1/pharmacy/distributor/stocks/products/flash/"
        params = {
            "flash_products": "true",
            "trending_products": "false",
            "recent_orders": "false",
        }
        self.client.get(
            url,
            name="pharmacy.distributor-sales-able-stock-product.list.flash",
            headers=self.headers,
            params=params,
        )

    @task
    def distributor_stock_details(self):
        # Stock products response
        json_data = self.stock_product_response.json()
        if "results" in json_data and json_data["results"]:
            stock_product_alias = json_data["results"][0].get("alias")
        if stock_product_alias:
            stock_product_alias = stock_product_alias

        url = f"/api/v1/pharmacy/distributor/stocks/products/{stock_product_alias}/"
        self.client.get(url, name="distributor-stock-details", headers=self.headers)

    @task
    def order_processing_items(self):
        url = "/api/v1/pharmacy/ecommerce/order/processing-items/"
        self.client.get(
            url, name="distributor-order-processing-item-list", headers=self.headers
        )

    @task
    def distributor_sales_able_stock_trending_product_list(self):
        url = "/api/v1/pharmacy/distributor/stocks/products/trending/"
        response = self.client.get(
            url,
            name="pharmacy.distributor-sales-able-stock-product.list.trending",
            headers=self.headers
        )

    @task
    def distributor_product_order_limit_by_alias(self):
        stock_alias = None

        stock_product_url = "/api/v1/search/pharmacy/stock/products/e-com/"
        stock_product_response = self.client.get(
            stock_product_url, name="ecom_product_search_es", headers=self.headers
        )

        json_data = stock_product_response.json()
        if "results" in json_data and json_data["results"]:
            stock_alias = json_data["results"][0].get("alias")
        if stock_alias:
            stock_alias = stock_alias

        url = f"/api/v1/pharmacy/distributor/product/order-limit/{stock_alias}/"
        self.client.get(
            url,
            name='distributor-product-order-limit',
            headers=self.headers
        )

    def distributor_order_retrieve(self):
        json_data = self.distributor_order_response.json()
        if "results" in json_data and json_data["results"]:
            distributor_order_alias = json_data["results"][0].get("alias")
        if distributor_order_alias:
            distributor_order_alias = distributor_order_alias
        url = f"/api/v1/pharmacy/distributor/order/{distributor_order_alias}/"
        self.client.get(url, name="distributor-order-details", headers=self.headers)

    # @task
    # def distributor_order_update(self):
    #     if self.distributor_order_response:
    #         json_data = self.distributor_order_response.json()
    #         if "results" in json_data and json_data["results"]:
    #             distributor_order_alias = json_data["results"][0].get("alias")

    #         if distributor_order_alias:
    #             distributor_order_alias = distributor_order_alias

    #             url = f"/api/v1/pharmacy/distributor/order/{distributor_order_alias}/"

    #             # Send a GET request to the endpoint
    #             get_distributor_order_detail_response = self.client.get(
    #                 url, name="distributor-order-details", headers=self.headers
    #             )

    #             # Validate the GET response against the expected values
    #             assert get_distributor_order_detail_response.status_code == 200

    #             # Send a PATCH request to the endpoint
    #             patch_response = self.client.patch(
    #                 url,
    #                 name="distributor-order-details",
    #                 headers=self.post_headers,
    #                 json=payload.distributor_order_update_payload,
    #             )
    #             # Validate the PATCH response against the expected values
    #             assert patch_response.status_code == 200

    #             patch_api_response = patch_response.json()

    #             assert (
    #                 patch_api_response["current_order_status"]
    #                 == payload.distributor_order_update_payload["current_order_status"]
    #             )
    #             assert (
    #                 patch_api_response["additional_cost"]
    #                 == payload.distributor_order_update_payload["additional_cost"]
    #             )
    #             assert (
    #                 patch_api_response["additional_cost_rate"]
    #                 == payload.distributor_order_update_payload["additional_cost_rate"]
    #             )

    @task
    def me_api_retrieve(self):
        url = "/api/v1/me/"
        self.client.get(url, name="me-details", headers=self.headers)

    # @task
    # def me_api_patch(self):
    #     url = "/api/v1/me/"
    #     details_update_payload = {"language": "en"}
    #     patch_response = self.client.patch(
    #         url,
    #         name="me-details",
    #         headers=self.post_headers,
    #         json=details_update_payload,
    #     )
    #     patch_api_response = patch_response.json()
    #     assert patch_api_response["language"] == details_update_payload["language"]

    @task
    def push_token_get_api(self):
        url = "/api/v1/notification/register-push-token/"
        self.client.get(url, name="resister-push-token", headers=self.headers)

    # @task
    # def push_token_post_api(self):
    #     url = "/api/v1/notification/register-push-token/"
    #     self.client.post(
    #         url,
    #         name="resister-push-token",
    #         headers=self.post_headers,
    #         json=payload.push_token_payload,
    #     )

    @task
    def product_restock_reminder_list(self):
        url = "/api/v1/pharmacy/product-restock-reminder/items/"
        name = "organization-wise-product-restock-reminder-list"
        self.client.get(url, name=name, headers=self.headers)

    @task
    def distributor_stock_product_list_v2(self):
        url = "/api/v2/pharmacy/distributor/stocks/products/recent/"
        name = "distributor-stock-product-list-recent-v2"
        self.client.get(url, name=name, headers=self.headers)

    @task
    def invoice_group_status_change_log(self):
        invoice_group_url = "/api/v1/ecommerce/invoice-groups/"
        name = "invoice-group-list"
        invoice_group_list_response = self.client.get(
            invoice_group_url, name=name, headers=self.headers
        )

        json_data = invoice_group_list_response.json()
        if "results" in json_data and json_data["results"]:
            invoice_group_alias = json_data["results"][0].get("alias")
            url = f"/api/v1/ecommerce/invoice-groups/status-change-log/{invoice_group_alias}/"
            response = self.client.get(
                url, name="invoice-group-fetch-all-status-change", headers=self.headers
            )

    @task
    def organization_wishlist_items(self):
        url = "/api/v1/ecommerce/wishlist-items/"
        name = "wishlist-item-view-by-organization"
        self.client.get(url, name=name, headers=self.headers)

    @task
    def organization_wishlist_items_stock_alias_list(self):
        url = "/api/v1/ecommerce/wishlist-items/stocks/"
        name = "wishlist-items-stock-alias-list"
        self.client.get(url, name=name, headers=self.headers)

    @task
    def organization_settings(self):
        url = "/api/v1/users/organizations/settings/"
        name = "organization-settings"
        self.client.get(url, name=name, headers=self.headers)

    @task
    def product_sorting_option_v2(self):
        url = "/api/v2/pharmacy/distributor/stocks/products/get-sorting-options/"
        name = "get-product-sorting-options-v2"
        self.client.get(url, name=name, headers=self.headers)


    @task
    def load_discount_rules(self):
        url = "/api/v1/pharmacy/get-discount-rules/"
        self.client.get(url, name="get-discount-rules", headers=self.headers)

    # @task
    # def user_registration(self):
    #     url = "/api/v1/users/ecom/register/"

    #     response = self.client.post(url, data=payload.user_payload, headers=self.headers)
    #     print(response)
    #     print(response.json())
    #     assert response.status_code == status.HTTP_201_CREATED


    @task
    def invoice_group_statistic(self):
        url = "/api/v1/ecommerce/invoice-group/statistics/?period=tm"
        name = "invoice-group-statistics"

        self.client.get(
            url,
            name=name,
            headers=self.headers
        )

    # @task
    # def mark_notification_as_read(self):
    #     url = "/api/v1/notification/mark-all-as-read/"
    #     name = "mark-all-notification-as-read"

    #     self.client.post(
    #         url,
    #         name=name,
    #         headers=self.headers
    #     )

    @task
    def distributor_stocks_products_best_discount(self):
        url = "/api/v2/pharmacy/distributor/stocks/products/best-discount/"
        distributor_stocks_products_best_discount_response = self.client.get(
            url,
            name="distributor-stock-product-list-best-discount-v2",
            headers=self.headers
        )

    @task
    def ecommerce_order_rating(self):
        url = "/api/v1/ecommerce/order-rating/"
        ecommerce_order_rating_response = self.client.get(
            url,
            name="invoice-groups-order-rating",
            headers=self.headers
        )
        self.ecommerce_order_rating_response = ecommerce_order_rating_response

    @task
    def user_notifications(self):
        url = "/api/v1/notification/user/notifications/"
        user_notifications_response = self.client.get(
            url,
            name="user-notification-list",
            headers=self.headers
        )

    @task
    def supplier_purchase_products_received(self):
        url = "/api/v1/pharmacy/supplier/purchase/products/received/"
        self.client.get(
            url,
            name="supplier-product-received",
            headers=self.headers
        )

    @task
    def distributor_stocks_similar_products(self):
        url = f"/api/v1/pharmacy/distributor/stocks/{self.stock_alias}/similar-products/"
        self.client.get(
            url,
            name="pharmacy.distributor-sales-able-stock-product.list.similar",
            headers=self.post_headers,
        )

    @task
    def distributor_stocks_recommended_products(self):
        url = f"/api/v1/pharmacy/distributor/stocks/{self.stock_alias}/recommended-products/"
        self.client.get(
            url,
            name="pharmacy.distributor-sales-able-stock-product.list.recommended",
            headers=self.post_headers,
        )
