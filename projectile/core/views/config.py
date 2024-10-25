from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class BackendConfig(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        response = {
            # 'CSRF_TOKEN': csrf(request),
            'STATIC_URL': '//exampledomaindotcom.s3.amazonaws.com/',
            'COUNTRY': 'bd',
            'LANGUAGE': 'en'
        }
        return Response(response)
