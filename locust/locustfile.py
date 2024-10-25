from locust import task

from base import BaseWebTasks


class SearchAppWebTasks(BaseWebTasks):
    @task
    def ecom_product_search_es(self):
        url = f"/api/v1/search/pharmacy/stock/products/e-com/?keyword={self.get_keyword()}"
        self.client.get(url, name="ecom_product_search_es", headers=self.headers)

    @task
    def product_change_log(self):
        url = "/api/v1/search/pharmacy/product/form/"
        self.client.get(url, name="pharmacy.product.form-list", headers=self.headers)

    @task
    def product_manufacturer_list(self):
        url = "/api/v1/search/pharmacy/product/manufacturer/"
        self.client.get(
            url, name="pharmacy.product.manufacturer-list", headers=self.headers
        )

    @task
    def product_group_list(self):
        url = "/api/v1/search/pharmacy/product/group/"
        self.client.get(url, name="pharmacy.product.group-list", headers=self.headers)

    @task
    def product_subgroup_list(self):
        url = "/api/v1/search/pharmacy/product/subgroup/"
        self.client.get(
            url, name="pharmacy.product.subgroup-list", headers=self.headers
        )

    @task
    def product_generic_list(self):
        url = "/api/v1/search/pharmacy/product/generic/"
        self.client.get(url, name="pharmacy.product.generic-list", headers=self.headers)

    @task
    def product_purchase_list(self):
        url = "/api/v1/search/pharmacy/product/purchase/"
        self.client.get(
            url, name="pharmacy.product.purchase-list", headers=self.headers
        )

    @task
    def product_category_list(self):
        url = "/api/v1/search/pharmacy/product/category/"
        self.client.get(
            url, name="pharmacy.product.category-list", headers=self.headers
        )

    @task
    def product_purchase_order_pending_list(self):
        url = "/api/v1/search/pharmacy/product/purchase-order-pending/"
        self.client.get(
            url, name="pharmacy.purchase-purchase-order", headers=self.headers
        )

    @task
    def product_purchase_order_completed_list(self):
        url = "/api/v1/search/pharmacy/product/purchase-order-completed/"
        self.client.get(
            url, name="pharmacy.purchase-purchase-order-completed", headers=self.headers
        )

    @task
    def product_purchase_order_discarded_list(self):
        url = "/api/v1/search/pharmacy/product/purchase-order-discarded/"
        self.client.get(
            url, name="pharmacy.purchase-purchase-order-discarded", headers=self.headers
        )

    @task
    def product_purchase_requisition_list(self):
        url = "/api/v1/search/pharmacy/product/purchase-requisition/"
        self.client.get(
            url, name="pharmacy.purchase-requisition-list", headers=self.headers
        )

    @task
    def product_distributor_order_list(self):
        url = "/api/v1/search/pharmacy/distributor/orders/"
        self.client.get(url, name="distributor-order-list-create", headers=self.headers)

    @task
    def stock_products_suggestions(self):
        url = "/api/v1/search/pharmacy/stock/products/suggestions/"
        self.client.get(
            url, name="pharmacy.stock-search.suggestions", headers=self.headers
        )

    @task
    def stock_products_unit(self):
        url = "/api/v1/search/pharmacy/unit/"
        self.client.get(url, name="pharmacy.unit-search", headers=self.headers)