from django.conf import settings
from django.urls import include, re_path
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView
)

from core.views.change_password import PasswordChangeView
from core.views.private import TokenObtainPairCustomView

admin.autodiscover()
admin.site.enable_nav_sidebar = False
admin.site.site_header = "HealthOS E-Commerce Admin"
admin.site.index_title = "HealthOS E-Commerce Administration Portal"

urlpatterns = [
    # Only for the logged in user
    re_path(r'^api/v1/me/', include('core.urls.me')),
    # Person api endpoint
    # url(r'^api/v1/users/', include('core.urls.users')),
    re_path(r'^api/v1/users/', include('core.urls.base')),
    re_path(r'^api/v1/pharmacy/', include('pharmacy.urls.v1')),
    re_path(r'^api/v2/pharmacy/', include('pharmacy.urls.v2')),
    # url(r'^api/v1/payment/', include('payment_gateway.urls')),
    re_path(r'^api/v1/notification/', include('expo_notification.urls')),
    re_path(r'^api/v1/deliveries/', include('delivery.urls')),
    re_path(r'^api/v1/ecommerce/', include('ecommerce.urls.base')),
    re_path(r'^api/v1/procurement/', include('procurement.urls')),
    re_path(r'^api/v1/promotion/', include('promotion.urls')),
    path("api/v1/search/areas/", include("search.url.area")),
    re_path(r'^api/v1/search/users/', include('search.url.users')),
    re_path(r'^api/v1/search/pharmacy/', include('search.url.pharmacy_search')),
    re_path(r'^api/v1/search/ecommerce/', include('search.url.ecommerce')),
    re_path(r'^api/v1/search/procurement/', include('search.url.procures')),
    re_path(r'api/v1/deep-link/', include('deep_link.urls.base')),
    # search common path
    re_path(r"api/v1/search", include("search.url")),
    # search V2
    re_path(r'^api/v2/search/pharmacy/', include('search.url.pharmacy_search_v2')),
    #order v2
    re_path(r'^api/v2/distributor/order/', include('order.urls.base')),
    # Notebooks
    re_path(r'^api/v1/notebooks/', include('notebookapi.rest.urls')),

    # the api auth part
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # Djoser urls
    # re_path(r'^api/v1/auth/', include('djoser.urls')),
    path(
        'api/v1/auth/users/set_password/',
        PasswordChangeView.as_view(),
        name='set_password'
    ),
    path("api/v1/delivery-hub/", include("core.urls.delivery_hub"), name="delivery_hub"),
    # Delivary Area URLS
    path("api/v1/areas/", include("core.urls.area"), name="delivery-area"),

    # Proxy
    path("api/v1/proxy/", include("reporter_proxy.urls"), name="proxy"),

    # simplejwt urls(login by email/phone, field name id, password)
    # path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/', TokenObtainPairCustomView.as_view(),
        name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # the django admin part
    re_path(r'^admin-8d81a5be-0a61-400f-b405-73af34df6972/', admin.site.urls),
]

if 'heartbeat' in settings.INSTALLED_APPS:
    from heartbeat.urls import urlpatterns as heartbeat_urls

    urlpatterns += [
        re_path(r'^heartbeat/', include(heartbeat_urls))
    ]

# urlpatterns += static(settings.INVOICE_URL, document_root=settings.INVOICES_STORE)
if settings.ENABLE_API_DOC:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns += [
        # Docs
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            'api/docs/',
            SpectacularSwaggerView.as_view(url_name='swagger-ui',),
            name='swagger-ui'
        ),
        path(
            "api/redocs/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

if settings.DEBUG:

    if settings.ENABLE_TOOLBAR:
        import debug_toolbar
        urlpatterns += [re_path(r'^debug/', include(debug_toolbar.urls))]
    if settings.ENABLE_SILK:
        urlpatterns += [re_path(r'^profiler/', include('silk.urls', namespace='silk'))]


    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
