from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework.views import APIView
from ..permissions import (
    IsSuperUser,
    AnyLoggedInUser,
    StaffIsTelemarketer,
    CheckAnyPermission,
)


from ..serializers import (
    CountryListSerializer,
    DateFormatSerializer,
)

from ..models import (
    Organization,
)

from ..enums import DhakaThana

from ..utils import (
    getCountryList,
    get_date_format_list,
)


class CountryList(generics.ListAPIView):
    permission_classes = (AnyLoggedInUser,)
    serializer_class = CountryListSerializer

    def get_queryset(self):
        return getCountryList()


class DateFormatList(generics.ListAPIView):
    pagination_class = None
    permission_classes = (AnyLoggedInUser,)
    serializer_class = DateFormatSerializer

    def get_queryset(self):
        return get_date_format_list()

class DeliveryAreaList(APIView):

    permission_classes = ()

    def get(self, request):
        keyword = self.request.query_params.get('keyword', None)
        data = DhakaThana().get_as_dict()
        search_results = {}
        if not keyword:
            return Response(data, status=status.HTTP_200_OK)
        for key in data.keys():
            if key.find(keyword.upper()) > -1:
                search_results[key] = data[key]
        return Response(search_results, status=status.HTTP_200_OK)


class SimilarOrganizationListByAreaWithMatchingScore(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request, organization_alias):
        matching_score = int(
            self.request.query_params.get('matching_score', 70))
        results = []
        if organization_alias:
            organization = Organization.objects.only(
                'id').get(alias=organization_alias)
            results = organization.get_similar_organization_list(
                matching_score)
        return Response(results, status=status.HTTP_200_OK)
