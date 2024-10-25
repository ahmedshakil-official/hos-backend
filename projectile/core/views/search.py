from django.db.models import Q
from rest_framework.generics import ListAPIView
from common.enums import Status, PublishStatus


class OrganizationAndGlobalWiseSearch(ListAPIView):
    def serve_queryset(self, view):
        model_name = getattr(view, "model_name", [])
        return model_name.objects.filter(
            Q(organization=self.request.user.organization) |
            ~Q(is_global__in=[PublishStatus.PRIVATE])
        ).filter(
            name__icontains=self.request.GET.get('keyword'),
            status=Status.ACTIVE
        ).order_by('pk')


class OrganizationWiseSearch(ListAPIView):
    def serve_queryset(self, view):
        model_name = getattr(view, "model_name", [])
        return model_name.objects.filter(
            name__icontains=self.request.GET.get('keyword'),
            organization=self.request.user.organization,
            status=Status.ACTIVE
        ).order_by('pk')

    def get_queryset(self):
        return self.serve_queryset(self)
