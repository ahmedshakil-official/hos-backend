from rest_framework import generics, status
from rest_framework.response import Response
from ..permissions import (
    IsSuperUser,
    StaffIsAdmin,
    StaffIsTelemarketer,
    CheckAnyPermission,
    StaffIsDistributionT3,
    StaffIsSalesManager,
)
from datetime import date


from .common_view import (
    CreateAPICustomView,
)

from ..serializers import (
    DistributorBuyerOrderSummarySerializer,
    DistributorBuyerOrderHistorySerializer,
)
from common.enums import Status

from ..models import (
    Person,
    Organization,
    PersonOrganization,
)
from ..enums import PersonGroupType
from django.db import transaction

from common import helpers
import random
import string
import os
from django.contrib.auth.hashers import make_password
from common.tasks import (
    send_sms,
    send_message_to_slack_or_mattermost_channel_lazy,
    cache_expire_list,
)
from pharmacy.enums import PurchaseType, OrderTrackingStatus, DistributorOrderType
from core.enums import OrganizationType
from pharmacy.models import Sales, Purchase
from core.custom_serializer.person import PersonModelSerializer
from core.custom_serializer.organization import DistributorBuyerOrganizationMergeSerializer


class DistributorBuyerOrderSummary(generics.ListAPIView):
    serializer_class = DistributorBuyerOrderSummarySerializer
    permission_classes = (IsSuperUser,)

    def get_queryset(self):
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        if not start_date or not end_date:
            start_date = str(helpers.get_date_from_period('1w'))
            end_date = str(date.today())
        queryset_template = '''SELECT data.*,
                Now() - registration AS registration_since,
                Now() - last_order   AS order_since
            FROM   (SELECT *
                    FROM   (SELECT id,
                                NAME,
                                Date(created_at) AS registration
                            FROM   core_organization co
                            WHERE  type = {0}) AS data1
                        LEFT JOIN (SELECT organization_id          AS id,
                                            order_number,
                                            amount,
                                            Date(Max(purchase_date)) AS last_order,
                                            Date(Min(purchase_date)) AS first_order
                                    FROM   (SELECT organization_id,
                                                    Count(id)        AS order_number,
                                                    Sum(grand_total) AS amount
                                            FROM   (SELECT data.*
                                                    FROM   (SELECT id,
                                                                    organization_id,
                                                                    grand_total,
                                                                    purchase_date
                                                            FROM   pharmacy_purchase pp
                                                            WHERE  purchase_type = {1}
                                                                    AND purchase_date
                                                                        BETWEEN
                                                                        '{2}' AND
                                                                        '{3}')
                                                            AS data
                                            LEFT JOIN pharmacy_ordertracking
                                                    ON data.id =
                        pharmacy_ordertracking.order_id
                                                    WHERE  order_status NOT IN ( {4}, {5} ))
                                                    AS data2
                                            GROUP  BY organization_id) AS data1
                                            LEFT JOIN (SELECT data.*
                                                        FROM   (SELECT id,
                                                                    organization_id,
                                                                    grand_total,
                                                                    purchase_date
                                                                FROM   pharmacy_purchase pp
                                                                WHERE  purchase_type = {1}) AS
                                                            data
                                            LEFT JOIN pharmacy_ordertracking
                                                    ON data.id =
                        pharmacy_ordertracking.order_id
                                                        WHERE  order_status NOT IN ( {4}, {5} ))
                                                    AS
                                                    data2 using
                                            (
                                            organization_id)
                                    GROUP  BY organization_id,
                                                order_number,
                                                amount) AS data2 using(id)) AS data '''
        queryset_template = queryset_template.format(
            OrganizationType.DISTRIBUTOR_BUYER,
            PurchaseType.VENDOR_ORDER,
            start_date,
            end_date,
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED
        )
        data = Organization.objects.raw(queryset_template)
        return list(data)


class DistributorBuyerOrderHistory(generics.ListAPIView):
    serializer_class = DistributorBuyerOrderHistorySerializer
    permission_classes = (StaffIsAdmin,)

    def get_queryset(self):
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        if not start_date or not end_date:
            start_date = str(helpers.get_date_from_period('1w'))
            end_date = str(date.today())
        queryset_template = '''SELECT   organization_id AS id,
         NAME,
         registered,
         primary_mobile,
         order_number,
         ordered_on_days,
         order_value,
         last_order,
         last_order_days_ago
FROM     (
                SELECT *
                FROM   (
                              SELECT data.* ,
                                     date(Now() + interval '6 hour') - last_order AS last_order_days_ago
                              FROM   (
                                              SELECT   organization_id,
                                                       NAME,
                                                       registered,
                                                       primary_mobile,
                                                       count(order_id)               AS order_number ,
                                                       count(DISTINCT purchase_date) AS ordered_on_days,
                                                       sum(grand_total)              AS order_value,
                                                       max(purchase_date)            AS last_order
                                              FROM     (
                                                                       SELECT DISTINCT organization_id,
                                                                                       NAME,
                                                                                       registered,
                                                                                       primary_mobile,
                                                                                       purchase_date,
                                                                                       order_id,
                                                                                       grand_total
                                                                       FROM            (
                                                                                                 SELECT    organization.*,
                                                                                                           date(organization.created_at + interval '6 hour')         AS registered,
                                                                                                           pharmacy_purchase.id                                      AS order_id,
                                                                                                           date(pharmacy_purchase.purchase_date + interval '6 hour') AS purchase_date,
                                                                                                           pharmacy_purchase.grand_total
                                                                                                 FROM      (
                                                                                                                  SELECT id AS organization_id,
                                                                                                                         NAME,
                                                                                                                         primary_mobile ,
                                                                                                                         created_at
                                                                                                                  FROM   core_organization
                                                                                                                  WHERE  type = {0}
                                                                                                                  AND status = {4} ) AS organization
                                                                                                 LEFT JOIN pharmacy_purchase
                                                                                                 using     (organization_id)
                                                                                                 WHERE     pharmacy_purchase.status = {1} ) AS purchase
                                                                       LEFT JOIN       pharmacy_ordertracking
                                                                       using           (order_id)
                                                                       WHERE           order_status NOT IN ({2},{3}) ) AS data
                                              GROUP BY organization_id,
                                                       NAME,
                                                       registered,
                                                       primary_mobile ) AS data ) AS data
                UNION
                SELECT id AS organization_id,
                       NAME,
                       date(created_at + interval '6 hour') AS registered,
                       primary_mobile,
                       0    AS order_number,
                       0    AS ordered_on_days,
                       0    AS order_value,
                       NULL AS last_order,
                       -1   AS last_order_days_ago
                FROM   core_organization co
                WHERE  id NOT IN
                                  (
                                  SELECT DISTINCT organization_id
                                  FROM            (
                                                                  SELECT DISTINCT organization_id,
                                                                                  NAME,
                                                                                  primary_mobile,
                                                                                  purchase_date,
                                                                                  order_id,
                                                                                  grand_total
                                                                  FROM            (
                                                                                            SELECT    organization.*,
                                                                                                      pharmacy_purchase.id                                      AS order_id,
                                                                                                      date(pharmacy_purchase.purchase_date + interval '6 hour') AS purchase_date,
                                                                                                      pharmacy_purchase.grand_total
                                                                                            FROM      (
                                                                                                             SELECT id AS organization_id,
                                                                                                                    NAME,
                                                                                                                    primary_mobile
                                                                                                             FROM   core_organization
                                                                                                             WHERE  type = {0}
                                                                                                             AND    status = {4}) AS organization
                                                                                            LEFT JOIN pharmacy_purchase
                                                                                            using     (organization_id)
                                                                                            WHERE     pharmacy_purchase.status = {1} ) AS purchase
                                                                  LEFT JOIN       pharmacy_ordertracking
                                                                  using           (order_id)
                                                                  WHERE           order_status NOT IN ({2},{3}) ) AS data)
                AND    type = {0} ) AS data
ORDER BY id '''
        queryset_template = queryset_template.format(
            OrganizationType.DISTRIBUTOR_BUYER,
            Status.DISTRIBUTOR_ORDER,
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
            Status.ACTIVE
        )
        data = Organization.objects.raw(queryset_template)
        return list(data)


class DistributorOrganizationCredential(generics.ListAPIView):
    serializer_class = PersonModelSerializer.DistributorBuyerUserCredential
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDistributionT3,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        organization_alias = self.kwargs.get('organization_alias', None)
        organization_permitted_user = Person.objects.only(
            'id',
            'alias',
            'phone',
            'first_name',
            'last_name',
        ).filter(
            status=Status.ACTIVE,
            organization__alias=organization_alias,
            # organization__type=OrganizationType.DISTRIBUTOR_BUYER,
            person_group=PersonGroupType.EMPLOYEE
        )

        return organization_permitted_user

    def post(self, request, *args, **kwargs):
        try:
            organization_alias = self.kwargs.get('organization_alias', None)
            person_alias = self.request.data.get('person', None)
            user = Person.objects.only(
                'id',
                'alias',
                'organization',
                'first_name',
                'last_name',
                'phone',
            ).get(
                alias=person_alias,
                organization__alias=organization_alias
            )
            url = "https://ecom.healthosbd.com"
            full_name = "{} {}".format(user.first_name, user.last_name)
            phone = helpers.generate_phone_no_for_sending_sms(user.phone)
            random_pass = "".join(random.choice(string.digits) for _ in range(6))
            user.password = make_password(random_pass)
            user.save(update_fields=['password'])
            sms_text = "Dear {},\nPlease goto {} and login with following credential.\nPhone: {},\nPassword: {}.".format(
                full_name, url, user.phone, random_pass
            )
            healthos_sms_text = """Password reset successful, \nPharmacy Name: {}, \nUser: {}, \nMobile: {}
            """.format(user.organization.name, full_name, phone)
            # Sending sms to client
            send_sms.delay(
                phone,
                sms_text,
                user.organization.id
            )
            # Send message to slack channel
            send_message_to_slack_or_mattermost_channel_lazy.delay(
                os.environ.get('HOS_PASSWORD_RESET_REQUEST_CHANNEL_ID', ""),
                healthos_sms_text
            )
            return Response(status=status.HTTP_200_OK)

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class DistributorBuyerOrganizationMerge(CreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DistributorBuyerOrganizationMergeSerializer

    def replace_all_employee(self, organization_to_keep, organization_to_inactive):
        # find all employee of clone organization and replace organization
        po_employees = PersonOrganization.objects.filter(
            status__in=[Status.ACTIVE, Status.DRAFT],
            organization=organization_to_inactive,
            person_group=PersonGroupType.EMPLOYEE,
        )
        for po_employee in po_employees:
            po_employee.organization = organization_to_keep
            po_employee.person.organization = organization_to_keep
            po_employee.save(update_fields=['organization', ])
            po_employee.person.save(update_fields=['organization', ])

        employees = Person.objects.filter(
            status__in=[Status.ACTIVE, Status.DRAFT],
            organization=organization_to_inactive,
            person_group=PersonGroupType.EMPLOYEE,
        )
        for employee in employees:
            employee.organization = organization_to_keep
            employee.save(update_fields=['organization', ])

    def inactive_buyers(self, organization_to_keep, organization_to_inactive, distributor_org_id):
        # find all patient/buyer of clone organization and inactive
        po_buyers = PersonOrganization.objects.filter(
            status=Status.ACTIVE,
            organization__id=distributor_org_id,
            buyer_organization=organization_to_inactive,
            person_group=PersonGroupType.PATIENT,
        )
        po_buyers.update(
            status=Status.INACTIVE
        )

        buyers = Person.objects.filter(
            status=Status.ACTIVE,
            organization__id=distributor_org_id,
            person_group=PersonGroupType.PATIENT,
            person_organization__buyer_organization=organization_to_inactive
        )
        buyers.update(
            status=Status.INACTIVE
        )

    def replace_orders_and_groups(self, organization_to_keep, organization_to_inactive):
        # find all order and order groups of clone organization and replace organization
        from pharmacy.models import DistributorOrderGroup
        order_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "organization": organization_to_inactive
        }
        orders = Purchase.objects.filter(**order_filters)
        orders_pk_list = list(orders.values_list('pk', flat=True))
        key_list = ['purchase_distributor_order_{}'.format(
            str(item).zfill(12)) for item in orders_pk_list]
        cache_expire_list.apply_async(
            (key_list, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        orders.update(organization=organization_to_keep)
        helpers.custom_elastic_rebuild(
            'pharmacy.models.Purchase', {'id__in': orders_pk_list})

        order_groups = DistributorOrderGroup.objects.filter(
            order_type=DistributorOrderType.ORDER,
            organization=organization_to_inactive
        )
        order_groups.update(organization=organization_to_keep)

    def update_sales(self, organization_to_keep, organization_to_inactive, distributor_org_id):
        # find all sales of clone organization and update for new organization
        org_buyer = organization_to_keep.get_org_buyer()
        org_buyer_person = org_buyer.person if org_buyer else None
        sales = Sales.objects.filter(
            organization__id=distributor_org_id,
            buyer_organization=organization_to_inactive
        )
        sales_pk_list = list(sales.values_list('pk', flat=True))
        key_list = ['pharmacy_serializers_salessearchliteserializer_{}'.format(
            str(item).zfill(12)) for item in sales_pk_list]
        cache_expire_list.apply_async(
            (key_list, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        sales.update(
            buyer_organization=organization_to_keep,
            buyer=org_buyer_person,
            person_organization_buyer=org_buyer
        )
        helpers.custom_elastic_rebuild(
            'pharmacy.models.Sales', {'id__in': sales_pk_list})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            from django.conf import settings
            if settings.DEBUG:
                distributor_org_id = 41
            else:
                distributor_org_id = 303
            organization_to_keep = Organization.objects.get(
                pk=request.data.get('organization', None))
            organization_to_inactive = Organization.objects.get(
                pk=request.data.get('clone_organization', None))
            if organization_to_keep == organization_to_inactive:
                error_response = {
                    'status':'error',
                    'message':'Both organization can\'t be same for merging'
                }
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

            self.replace_all_employee(
                organization_to_keep, organization_to_inactive)
            self.inactive_buyers(
                organization_to_keep,
                organization_to_inactive, distributor_org_id
            )
            self.replace_orders_and_groups(
                organization_to_keep, organization_to_inactive)
            self.update_sales(
                organization_to_keep,
                organization_to_inactive,
                distributor_org_id
            )

            # Inactive org instance
            organization_to_inactive.status = Status.INACTIVE
            organization_to_inactive.save(update_fields=['status', ])

            # Update mother for keeping merge reference
            organization_to_keep.description = organization_to_inactive.pk
            organization_to_keep.save(update_fields=['description',])

            # Inactive settings
            settings_instance_of_inactive_org = organization_to_inactive.get_settings_instance()
            settings_instance_of_inactive_org.status = Status.INACTIVE
            settings_instance_of_inactive_org.save(update_fields=['status', ])
            response = {
                "message": "Success"
            }
            return Response(response, status=status.HTTP_201_CREATED)

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
