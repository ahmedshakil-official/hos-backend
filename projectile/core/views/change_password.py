from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from core.custom_serializer.change_password import PasswordChangeSerializer


class PasswordChangeView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(
            {'detail': _('PASSWORD_RESET_SUCCESSFULLY')},
            status=status.HTTP_200_OK,
        )
