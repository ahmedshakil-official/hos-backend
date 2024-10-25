
from django.db import transaction
from django.db.models import (
    Case,
    Count,
    IntegerField,
    Value,
    When
)
from django.db.models.functions import TruncDate
from django.db.utils import IntegrityError
from django.utils import timezone

from rest_framework import views, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.enums import Status
from common.helpers import to_boolean
from core.permissions import (
    CheckAnyPermission,
    StaffIsProcurementOfficer,
    StaffIsAdmin,
    IsSuperUser,
    StaffIsProcurementManager,
)
from core.views.common_view import(
    ListAPICustomView,
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView
)
from core.models import Organization
from .custom_serializer.promotion import (
    PromotionModelSerializer,
)
from .custom_serializer.published_promotion import (
    PublishedPromotionModelSerializer,
)
from .custom_serializer.popup_message import (
    PopUpMessageModelSerializer,
)
from .custom_serializer.published_popup_message import (
    PublishedPopUpMessageModelSerializer,
    PublishedPopUpMessageLogSerializer,
)
from .custom_serializer.published_promotion_order import (
    PublishedPromotionOrderModelSerializer,
)

from .models import (
    Promotion,
    PublishedPromotion,
    PopUpMessage,
    PublishedPopUpMessage,
    PublishedPromotionOrder,
)

class PromotionList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PromotionModelSerializer.List

    def get_queryset(self):
        return Promotion.objects.filter(status=Status.ACTIVE).order_by('-pk')


class PromotionDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = PromotionModelSerializer.List
    lookup_field = 'alias'


class PublishPromotion(ListCreateAPICustomView):
    """Published Promotion list in Current Organization"""
    available_permission_classes = (
        IsSuperUser,
    )
    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAuthenticated,
            )
        else:
            self.available_permission_classes = (IsSuperUser, )
        return (CheckAnyPermission(), )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PublishedPromotionModelSerializer.List
        return PublishedPromotionModelSerializer.Mini

    def get_queryset(self):
        claimed_promotions = PublishedPromotionOrder().get_active_from_organization(
            self.request.user.organization
        ).only(
            'published_promotion'
        ).values_list('published_promotion', flat=True).distinct()
        return super(PublishPromotion, self).get_queryset().filter(
            promotion__status=Status.ACTIVE,
        ).exclude(pk__in=claimed_promotions).select_related(
            'promotion',
        )


class PublishPopUpMessage(ListCreateAPICustomView):
    """Published PopUp Message list in Current Organization"""
    available_permission_classes = (
        IsSuperUser,
    )
    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAuthenticated,
            )
        else:
            self.available_permission_classes = (IsSuperUser, )
        return (CheckAnyPermission(), )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PopUpMessageModelSerializer.List
        return PublishedPopUpMessageModelSerializer.Lite

    def get_queryset(self, related_fields=None, only_fields=None):
        # Return only published messages
        published_messages = PublishedPopUpMessage().get_active_from_organization(
            self.request.user.organization_id
        ).only(
            'message'
        ).values_list('message', flat=True).distinct()
        queryset = PopUpMessage.objects.filter(status=Status.ACTIVE, pk__in=published_messages)
        return queryset.order_by("-pk")


class PromotionBulkPublish(views.APIView):
    available_permission_classes = (
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = PublishedPromotionModelSerializer.Basic

    def prepare_published_promotion(self, new_promotion, organizations):
        promotion_message, created = Promotion.objects.get_or_create(
            status=Status.ACTIVE,
            message=new_promotion
        )
        if created:
            promotion_message.save()
        data_list = []
        for organization in organizations:
            data_list.append({
                'organization': organization,
                'promotion': promotion_message.id
            })
        return data_list

    def unpublish_promotions(self, unpublish_promotion, unpublish_organizations):
        if unpublish_promotion and unpublish_organizations:
            filters = {
                "status": Status.ACTIVE,
                "promotion": unpublish_promotion,
                "organization__in": unpublish_organizations
            }
            published_promotions = PublishedPromotion.objects.filter(**filters)
            published_promotions.update(status=Status.INACTIVE)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # promotions format will be as (while providing promotion id and organization id)
        # promotions: [{'organization': <id>, 'promotion': <id>}, .... ]
        promotions = request.data.get('promotions', [])

        # while new promotion message for multiple organization
        # {"new_promotion": "<message text>", "organizations": [<org_id>, <org_id>]}
        new_promotion = request.data.get('new_promotion', None)
        organizations = request.data.get('organizations', [])
        # Promotion id want to unpublish
        unpublish_promotion = request.data.get('unpublish_promotion', None)
        # List of organizations wants to unpublish a promotion
        unpublish_organizations = request.data.get('unpublish_organizations', [])
        unpublish_all_organization = to_boolean(request.data.get('unpublish_all_organization', False))
        # if publish all organization is true publisth the message for all organization

        if unpublish_all_organization and not unpublish_organizations:
            unpublish_organizations = Organization.objects.filter(
                status=Status.ACTIVE
            ).values_list('pk', flat=True)
        try:
            with transaction.atomic():
                self.unpublish_promotions(
                    unpublish_promotion,
                    unpublish_organizations
                )
                if organizations and new_promotion:
                    promotions = self.prepare_published_promotion(new_promotion, organizations)

                serializer = self.serializer_class(
                    data=promotions, many=True, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    serializer.save(entry_by=self.request.user)
                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PopUpMessageList(ListCreateAPICustomView):
    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAuthenticated,
            )
        else:
            self.available_permission_classes = (
                IsSuperUser,
                StaffIsProcurementManager,
            )
        return (CheckAnyPermission(), )
    serializer_class = PopUpMessageModelSerializer.List

    def get_queryset(self):
        return PopUpMessage.objects.filter(
            status=Status.ACTIVE
        ).order_by('-pk')


class PopUpMessageDetails(RetrieveUpdateDestroyAPICustomView):
    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAuthenticated,
            )
        else:
            self.available_permission_classes = (
                IsSuperUser,
                StaffIsProcurementManager,
            )
        return (CheckAnyPermission(), )

    serializer_class = PopUpMessageModelSerializer.List
    lookup_field = 'alias'


class PopUpMessageBulkPublish(views.APIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = PublishedPopUpMessageModelSerializer.Basic

    def prepare_published_message(self, new_message, organizations):
        filters = {
            "status": Status.ACTIVE
        }
        if isinstance(new_message, int):
            filters['id'] = new_message
        else:
            filters['message'] = new_message
        popup_message, created = PopUpMessage.objects.get_or_create(
            **filters
        )
        if created:
            popup_message.save()
        data_list = []
        for organization in organizations:
            data_list.append({
                'organization': organization,
                'message': popup_message.id
            })
        return data_list

    def unpublish_messages(self, unpublish_message, unpublish_organizations):
        if unpublish_message and unpublish_organizations:
            filters = {
                "status": Status.ACTIVE,
                "message": unpublish_message,
                "organization__in": unpublish_organizations
            }
            published_messages = PublishedPopUpMessage.objects.filter(**filters)
            # if unpublish then set date as expire_date
            published_messages.update(status=Status.INACTIVE, expires_date=timezone.now())

            if unpublish_message:
                # update popup message last_unpublished_date
                popup_message = PopUpMessage.objects.get(id=unpublish_message)

                popup_message.last_unpublished_date = timezone.now()
                popup_message.save()

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Messages format will be as (while providing promotion id and organization id)
        # popup_messages: [{'organization': <id>, 'message': <id>}, .... ]
        popup_messages = request.data.get('messages', [])

        # while new promotion message for multiple organization
        # {"new_message": "<message text>", "organizations": [<org_id>, <org_id>]}
        # new_message can be a text(for create a new message) or integer(message id)
        new_message = request.data.get('new_message', None)
        organizations = request.data.get('organizations', [])
        # Unpublish message ID
        unpublish_message = request.data.get('unpublish_message', None)
        # Unpublish organizations list
        unpublish_organizations = request.data.get('unpublish_organizations', [])
        publish_all_organization = to_boolean(request.data.get('publish_all_organization', False))
        unpublish_all_organization = to_boolean(request.data.get('unpublish_all_organization', False))
        # if publish all organization is true publisth the message for all organization
        if publish_all_organization:
            organizations = Organization.objects.filter(
                status=Status.ACTIVE
            ).values_list('pk', flat=True)
        elif unpublish_all_organization and not unpublish_organizations:
            unpublish_organizations = Organization.objects.filter(
                status=Status.ACTIVE
            ).values_list('pk', flat=True)

        try:
            with transaction.atomic():
                self.unpublish_messages(
                    unpublish_message,
                    unpublish_organizations,
                )
                if organizations and new_message:
                    popup_messages = self.prepare_published_message(new_message, organizations)

                serializer = self.serializer_class(
                    data=popup_messages, many=True, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    serializer.save(entry_by=self.request.user)
                    # updating popup_message after banner is published
                    popup_message = PopUpMessage.objects.get(id=new_message)

                    # Check is there have any active published popup message exists for this popup_message
                    has_active_published_popup_message = popup_message.published_messages.filter(
                        status=Status.ACTIVE).exists()

                    popup_message.is_published = has_active_published_popup_message

                    if not popup_message.first_published_date and has_active_published_popup_message is True:
                        popup_message.first_published_date = timezone.now()

                    popup_message.save()

                    if publish_all_organization:
                        try:
                            message=PopUpMessage.objects.get(id=popup_messages[0]["message"])
                            message.is_public=True
                            message.save()
                        except PopUpMessage.DoesNotExist:
                            raise serializers.ValidationError("Message Not Found!")
                    if unpublish_all_organization:
                        try:
                            message=PopUpMessage.objects.get(id=new_message)
                            message.is_public=False
                            message.save()
                        except PopUpMessage.DoesNotExist:
                            raise serializers.ValidationError("Message Not Found!")

                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PublishedPromotionOrderList(ListCreateAPICustomView):
    """Order list form Published Promotion"""
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PublishedPromotionOrderModelSerializer.List
        return PublishedPromotionOrderModelSerializer.Basic

    def get_queryset(self):
        queryset = PublishedPromotionOrder.objects.filter(
            status=Status.ACTIVE,
            published_promotion__status=Status.ACTIVE
        ).select_related(
            'organization',
            'published_promotion__promotion',
        ).order_by('-pk')
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(organization=self.request.user.organization)


class PublishedPromotionOrderDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PublishedPromotionOrderModelSerializer.List
        return PublishedPromotionOrderModelSerializer.Basic

    def get_queryset(self):
        queryset = PublishedPromotionOrder.objects.filter(
            status=Status.ACTIVE
        )
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(organization=self.request.user.organization)


class PublishedPopUpMessageLogList(ListAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = None
    serializer_class = PublishedPopUpMessageLogSerializer

    def get_queryset(self, related_fields=None, only_fields=None):
        alias = self.kwargs.get("alias", None)
        queryset = (
            PublishedPopUpMessage.objects.filter(message__alias=alias)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                publish_count=Count(
                    Case(
                        When(status=Status.ACTIVE, then=Value(1)),
                        output_field=IntegerField(),
                    )
                ),
                unpublish_count=Count(
                    Case(
                        When(status=Status.INACTIVE, then=Value(1)),
                        output_field=IntegerField(),
                    )
                ),
            )
        )

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_log_count = queryset.count()

        serializer = self.get_serializer(queryset, many=True)

        response_data = {
            "total_log_count": total_log_count,
            "results": serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)
