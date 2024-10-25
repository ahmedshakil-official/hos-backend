from django.conf import settings

from rest_framework.generics import ListAPIView

from elasticsearch_dsl import Q

from common.healthos_helpers import HealthOSHelper
from pharmacy.serializers import ProductManufacturingCompanySerializer

from search.document.pharmacy_search import ProductManufacturerDocument


class TopManufacturer(ListAPIView):
    """
    ListAPIView for retrieving a list of top manufacturing companies with custom sorting.

    This view retrieves a list of top manufacturing companies based on predefined
    company IDs. The results are sorted in a custom order specified by the order
    of company IDs provided.

    Attributes:
        None

    Methods:
        get_queryset(self): Retrieve and return a list of top manufacturing
        companies sorted by the custom order of company IDs.

    """

    serializer_class = ProductManufacturingCompanySerializer

    def get_queryset(self):
        """
        Retrieve and return a list of top manufacturing companies sorted by custom order.

        This method constructs an Elasticsearch query to retrieve top manufacturing
        companies based on predefined company IDs. The results are sorted in a custom
        order specified by the order of company IDs provided.
        """
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )
        # Create a Search object
        search = ProductManufacturerDocument.search()

        # Get the list of top manufacturing company IDs
        company_ids = HealthOSHelper().get_top_manufacturing_company_pk_list()

        # Build the must query using Q objects
        query = Q("terms", _id=company_ids)

        # Excluding items which don't have a logo
        query = Q(
            "bool",
            must=[query],
            must_not=[~Q("exists", field="logo")],
        )

        # Apply the query to the search
        search = search.query(query)
        search = search.extra(size=len(company_ids))

        # Add a function score query to sort by custom order
        functions = []
        for idx, company_id in enumerate(company_ids):
            functions.append(
                {
                    "filter": Q("term", _id=company_id),
                    "weight": len(company_ids) - idx,
                }
            )
        function_score_query = {
            "functions": functions,
            "score_mode": "sum",
        }
        search = search.query("function_score", **function_score_query)

        # Execute the search with page size
        response = search.execute()

        return response
