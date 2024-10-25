import hashlib
from django.core.cache import caches
from django.core.paginator import Paginator
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination
from common.cache_keys import QS_COUNT_CACHE_KEY_PREFIX

def cached_count_queryset(queryset, timeout=60*60, cache_name='default'):
    """
        Return copy of queryset with queryset.count() wrapped to cache result for `timeout` seconds.
    """
    cache = caches[cache_name]
    if isinstance(queryset, list):
        real_count = lambda: len(queryset)
    else:
        queryset = queryset._chain()
        real_count = queryset.count
    try:
        model_name = queryset.model.__name__
    except:
        model_name = ""

    def count(queryset):
        try:
            cache_key = f"{QS_COUNT_CACHE_KEY_PREFIX}{model_name}:{hashlib.md5(str(queryset.query).encode('utf8')).hexdigest()}"

            # return existing value, if any
            value = cache.get(cache_key)
            if value is not None:
                return value

            # cache new value
            value = real_count()
            cache.set(cache_key, value, timeout)
        except:
            value = real_count()
        return value

    queryset.count = count.__get__(queryset, type(queryset))
    return queryset


class CachedCountPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    def paginate_queryset(self, queryset, *args, **kwargs):
        view = kwargs.get("view")
        timeout = 60 * 30
        if hasattr(view, "qs_count_timeout"):
            timeout = getattr(view, "qs_count_timeout")
        if hasattr(queryset, "count"):
            queryset = cached_count_queryset(queryset, timeout)
        return super().paginate_queryset(queryset, *args, **kwargs)

class FasterDjangoPaginator(Paginator):
    @cached_property
    def count(self):
        # only select 'id' for counting, much cheaper
        return self.object_list.values('id').count()

class FasterDjangoPaginatorWithDefaultCount(Paginator):
    @cached_property
    def count(self):
        return 999999999999


class FasterPageNumberPaginationWithDefaultCount(PageNumberPagination):
    page_size_query_param = 'page_size'
    django_paginator_class = FasterDjangoPaginatorWithDefaultCount

class FasterPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    django_paginator_class = FasterDjangoPaginator

class FasterPageNumberPaginationWithoutCount(PageNumberPagination):
    # django_paginator_class = FasterDjangoPaginatorWithoutCount
    def get_paginated_response(self, data):
        from rest_framework.response import Response
        from rest_framework import status

        return Response({
            # "code": status.HTTP_200_OK,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            # 'count': self.page.paginator.count,
            'results': data
        })

class CustomPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    # django_paginator_class = FasterDjangoPaginator

class ListPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        from rest_framework.response import Response
        from rest_framework import status

        return Response({
            "code": status.HTTP_200_OK,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })

class TwoHundredResultsSetPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 20
