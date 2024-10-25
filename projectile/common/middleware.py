from django_elasticsearch_dsl.apps import DEDConfig
from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from core.views.private import MeLogin
from pharmacy.views import PurchaseList
from pharmacy.view.purchase import (
    DistributorOrderCartListCreate,
    OrderStatusResponsiblePersonBulkCreate,
    DistributorOrderListCreate,
)

from ecommerce.views.order_invoice_group import (
    OrderInvoiceGroupListCreate,
    CloneOrderInvoiceGroup,
)

class CustomElasticController(MiddlewareMixin):
    from procurement.views.procure import CompletePurchase

    app_config = apps.get_app_config(DEDConfig.name)
    request_list = [
        PurchaseList,
        DistributorOrderCartListCreate,
        OrderStatusResponsiblePersonBulkCreate,
        DistributorOrderListCreate,
        MeLogin,
        OrderInvoiceGroupListCreate,
        CompletePurchase,
        CloneOrderInvoiceGroup,
    ]

    def process_response(self, request, response):
        self.app_config.signal_processor.setup()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(view_func, 'view_class'):
            if view_func.view_class in self.request_list:
                self.app_config.signal_processor.teardown()


class SerialCacheExpire(MiddlewareMixin):

    def process_response(self, request, response):
        if (hasattr(response, 'status_code')) and response.status_code == 400:
            if (hasattr(request, 'user')):
                user = request.user
                if (hasattr(user, 'organization')):
                    request.user.organization.expire_serial_cache()
        return response
