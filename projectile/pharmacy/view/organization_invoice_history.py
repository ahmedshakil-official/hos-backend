import json
from datetime import datetime, timedelta
from pytz import timezone
from tqdm import tqdm
import pandas as pd
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from common.enums import Status
from common.utils import prepare_datetime_by_timestamp
from core.views.common_view import (
    ListAPICustomView
)
from core.permissions import (
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsSalesman,
    CheckAnyPermission,
    IsSuperUser,
    StaffIsSalesManager,
)
from core.models import Organization, PersonOrganization
from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus
from pharmacy.models import Purchase


class OrganizationOrderInvoiceHistory(APIView):
    """Report to show product summary of accepted
        order of a distributor
    """
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsSalesManager
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        inactive_days = int(self.request.query_params.get('inactive_days', 3))
        thana_code = self.request.query_params.get('delivery_thana', '')
        sub_area = self.request.query_params.get('sub_area', '')
        referrer = self.request.query_params.get('responsible_employee', '')
        person_organizations = self.request.query_params.get('person_organizations', '')
        added_by = [item for item in person_organizations.split(',') if person_organizations]
        thana_codes = [item for item in thana_code.split(',') if thana_code]
        sub_areas = [item for item in sub_area.split(',') if sub_area]
        delivery_hub = self.request.query_params.get('delivery_hub', '')
        area_code = request.query_params.get("area_code", None)

        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "distributor" : self.request.user.organization_id,
        }
        organization_filter = {}
        if added_by:
            persons = PersonOrganization.objects.values_list(
                'person__alias', flat=True
            ).filter(alias__in=added_by)
            organization_filter['entry_by__alias__in'] = persons

        if referrer:
            organization_filter['referrer__alias'] = referrer

        if thana_codes:
            organization_filter['delivery_thana__in'] = thana_codes

        if sub_areas:
            organization_filter['delivery_sub_area__in'] = sub_areas

        if delivery_hub:
            organization_filter['delivery_hub__alias'] = delivery_hub
        if area_code:
            organization_filter["area__code__in"] = delivery_hub

        def days_pair(days_gap):
            days = days_gap
            now = datetime.now(timezone('Asia/Dhaka'))
            date_up = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_low = date_up - timedelta(days)
            return date_up, date_low

        def get_active_organization(days):

            date_up, date_low = days_pair(days)

            organization_lists = Purchase.objects.select_related(
                'distributor',
                'organization__entry_by',
                'distributor_order_group',
                'responsible_employee__designation__department',
            ).filter(
                **filters
            ).filter(
                purchase_date__gte=date_low,
                purchase_date__lte=date_up,
            ).select_related(
                'organization'
            ).values(
                'organization__id',
            ).distinct('organization__id')

            return organization_lists

        def get_ordered_once_organization():

            organization_lists = Purchase.objects.select_related(
                'distributor',
                'organization__entry_by',
                'distributor_order_group',
                'responsible_employee__designation__department',
            ).filter(
                **filters
            ).exclude(
                current_order_status__in=[
                    OrderTrackingStatus.REJECTED,
                    OrderTrackingStatus.CANCELLED,
                    OrderTrackingStatus.FULL_RETURNED
                ]
            ).select_related(
                'organization'
            ).values(
                'organization__id',
            ).distinct('organization__id')

            return organization_lists

        organization_ordered = get_ordered_once_organization()
        organization_active = get_active_organization(inactive_days)

        one_w_up, one_w_low = days_pair(7)
        one_m_up, one_m_low = days_pair(30)
        three_m_up, three_m_low = days_pair(90)
        one_y_up, one_y_low = days_pair(365)

        date_loop = [
            { 'up' : one_w_up, 'low' : one_w_low, 'key' : 'one_w' },
            { 'up' : one_m_up, 'low' : one_m_low, 'key' : 'one_m' },
            { 'up' : three_m_up, 'low' : three_m_low, 'key' : 'three_m' },
            { 'up' : one_y_up, 'low' : one_y_low, 'key' : 'one_y' },
        ]

        organization = Organization.objects.filter(
            status__in=[Status.ACTIVE, Status.INACTIVE, Status.SUSPEND],
            min_order_amount__lte=100000,
            # id__in=organization_ordered,
            **organization_filter
        ).exclude(
            # id__in=organization_active
        ).values(
            'id',
            'name',
            'address',
            'status',
            'min_order_amount',
            'delivery_thana',
            'delivery_sub_area',
            'primary_mobile',
            'created_at',
            'entry_by__first_name',
            'entry_by__last_name',
        )

        organization = pd.DataFrame(organization)
        if organization.empty:
            return Response([])

        organization['added_by'] = organization.get('entry_by__first_name', '') + " " + organization.get('entry_by__last_name', '')
        organization['one_w_invoice'] = None
        organization['one_w_days'] = None
        organization['one_w_amount'] = None
        organization['one_m_invoice'] = None
        organization['one_m_days'] = None
        organization['one_m_amount'] = None
        organization['three_m_invoice'] = None
        organization['three_m_days'] = None
        organization['three_m_amount'] = None
        organization['one_y_invoice'] = None
        organization['one_y_days'] = None
        organization['one_y_amount'] = None

        organization.rename(
            columns = {
                'created_at' : 'onborded_on',
                'delivery_sub_area' : 'sub_area',
                'primary_mobile' : 'mobile'
            },
            inplace=True
        )

        organization.drop(
            [
                'entry_by__last_name',
                'entry_by__first_name',
            ],
            inplace=True,
            axis=1
        )

        organization.onborded_on = organization.onborded_on.dt.tz_convert('Asia/Dhaka')
        organization.onborded_on = organization.onborded_on.dt.strftime('%Y-%m-%d')

        for i, row in organization.iterrows():

            organization_id = organization.at[i,'id']

            for dates in date_loop:
                order_data = Purchase.objects.select_related(
                ).filter(
                    **filters
                ).filter(
                    organization__id=organization_id,
                    purchase_date__gte=dates['low'],
                    purchase_date__lte=dates['up'],
                ).exclude(
                    current_order_status__in=[7, 8, 10]
                ).values(
                    'id',
                    'purchase_date',
                    'grand_total',
                )

                order_data = pd.DataFrame(order_data)

                order_days = 0
                order_invoice = 0
                order_value = 0
                if not order_data.empty:
                    order_data.purchase_date = order_data.purchase_date.dt.tz_convert('Asia/Dhaka')
                    order_data.purchase_date = order_data.purchase_date.dt.date
                    order_days = order_data['purchase_date'].nunique()
                    order_invoice = order_data['id'].nunique()
                    order_value = order_data['grand_total'].sum()


                invoice_key='{}_invoice'.format(dates['key'])
                amount_key='{}_amount'.format(dates['key'])
                days_key='{}_days'.format(dates['key'])

                organization.at[i, invoice_key] = order_invoice
                organization.at[i, amount_key] = order_value
                organization.at[i, days_key] = order_days

        data = organization.to_json(orient = 'records',)
        response_data = json.loads(data)
        return Response(response_data)