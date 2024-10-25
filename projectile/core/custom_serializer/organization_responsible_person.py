from rest_framework import status
from rest_framework.response import Response

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer
from common.enums import Status
from core.custom_serializer.organization import OrganizationMeta
from core.custom_serializer.person_organization import PersonOrganizationModelSerializer
from core.helpers import update_organization_responsible_employee_from_invoices
from ecommerce.models import OrderInvoiceGroup
from pharmacy.enums import OrderTrackingStatus


class PossibleResponsiblePerson:
    class List(ListSerializer):
        primary_responsible_person = PersonOrganizationModelSerializer.MinimalList()
        possible_primary_responsible_person = PersonOrganizationModelSerializer.MinimalList()

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'id',
                'primary_responsible_person',
                'possible_primary_responsible_person',
            )

    class Post(ListSerializer):
        class Meta(OrganizationMeta):
            fields = ()

        def create(self, validated_data):
            invoice_groups = OrderInvoiceGroup.objects.filter(
                status=Status.ACTIVE,
                responsible_employee__isnull=False,
            ).select_related('order_by_organization').values(
                'delivery_date',
                'responsible_employee',
                'order_by_organization'
            ).exclude(
                current_order_status__in=[
                    OrderTrackingStatus.REJECTED,
                    OrderTrackingStatus.CANCELLED
                ]
            ).order_by('-delivery_date').distinct('delivery_date', 'order_by_organization')

            organization_ids = update_organization_responsible_employee_from_invoices(invoice_groups)
            return Response(
                f"Updated the primary responsible employee of the organization IDs based {organization_ids}",
                status=status.HTTP_200_OK
            )
