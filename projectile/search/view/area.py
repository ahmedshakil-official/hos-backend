"""View for delivery area / Dhaka Thana."""

from django.conf import settings

from rest_framework.generics import ListAPIView

from elasticsearch_dsl import Q

from core.permissions import (
    CheckAnyPermission,
    AnyLoggedInUser,
)

from core.custom_serializer.area import AreaModelSerializer
from common.enums import Status
from ..document.area import AreaDocument


class AreaSearchView(ListAPIView):
    permission_classes = ()
    serializer_class = AreaModelSerializer.List

    def get_queryset(self):
        # Retrieve the search keyword and pagination size from request parameters
        query_value = self.request.query_params.get("keyword", None)
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )

        # Create an Elasticsearch search instance with a filter for active areas
        search = AreaDocument.search().filter("match", status=Status.ACTIVE)

        # Check if the query value is a digit (e.g., code search)
        if query_value and query_value.isdigit():
            # If a digit is provided, perform an exact match on the 'code' field
            search = search.query(
                "match",
                code=query_value,
            )
        elif query_value:
            # If not a digit, perform a fuzzy search for partial matching on the 'name' field
            search = search.query(
                "query_string",
                query=f"*{query_value}*",
                fields=["name"],
            )

        # Execute the search and retrieve the response, limiting the number of results
        response = search[: int(page_size)].execute()

        # Return the Elasticsearch response as queryset
        return response
