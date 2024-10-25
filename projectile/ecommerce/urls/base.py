from .invoice_group_delivery_sheet import (
    urlpatterns as url_invoice_group_delivery_sheet,
)
from .order_invoice_group import urlpatterns as url_order_invoice_group
from .short_return_log import urlpatterns as url_short_return_log
from .common import urlpatterns as url_common
from .delivery_sheet_invoice_group import (
    urlpatterns as url_delivery_sheet_invoice_group,
)
from .wishlist import urlpatterns as url_wishlist
from .order_tracking import urlpatterns as url_order_tracking
from .invoice_group_pdf import urlpatterns as url_invoice_group_pdf
from .invoice_pdf_group import urlpatterns as url_invoice_pdf_group


urlpatterns = (
    url_invoice_group_delivery_sheet
    + url_order_invoice_group
    + url_short_return_log
    + url_common
    + url_delivery_sheet_invoice_group
    + url_wishlist
    + url_order_tracking
    + url_invoice_group_pdf
    + url_invoice_pdf_group
)
