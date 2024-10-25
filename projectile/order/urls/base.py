from .cart import urlpatterns as url_cart
from .order import urlpatterns as url_order


urlpatterns = (
    url_cart +
    url_order
)
