import ast
import logging
import json
from datetime import timedelta

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    CharField,
    Min,
    Max, F,
)
from django.db.models.fields import DateField
from django.db.models.functions import Cast
from django.core.cache import cache

from common.cache_keys import NOTIFICATION_COUNT_USER_CACHE_KEY_PREFIX
from common.enums import Status
from common.helpers import to_boolean
from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsTelemarketer,
    StaffIsProcurementManager,
)
from core.models import Organization

from .serializers import (
    PushTokenSerializer,
    PushNotificationListSerializer,
    UserNotificationListSerializer, NotificationSerializer, UserNotificationDetailsSerializer,
)
from .models import PushToken, PushNotification, Notification
from .tasks import send_push_notification_to_mobile_app_by_org

logger = logging.getLogger(__name__)

class RegisterPushToken(ListCreateAPICustomView):
    available_permission_classes = (IsSuperUser, )
    permission_classes = (CheckAnyPermission,)

    serializer_class = PushTokenSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsSuperUser,
            )
        else:
            self.available_permission_classes = (
                IsAuthenticated,
            )
        return (CheckAnyPermission(),)

    def get_queryset(self):
        query = PushToken.objects.select_related(
            'user',
        ).filter(
            status=Status.ACTIVE,
            active=True
        ).order_by('-id')
        return query


class PushNotificationList(ListCreateAPICustomView):
    '''View for creating Custom Push Notification'''
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsTelemarketer,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PushNotificationListSerializer

    # pylint: disable=unused-argument
    def get_queryset(self):

        notifications = PushNotification.objects.filter().order_by('-created_at').values(
            'title',
            'body',
        ).annotate(
            organizations=ArrayAgg(Cast('user__organization__name', CharField()), distinct=True),
            date=Cast('created_at', DateField())
        )

        return notifications

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        id_of_queryset = queryset.values_list('id', flat=True)
        return self.get_from_cache(
            queryset=id_of_queryset,
            request=request
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            # Notification data
            notification_title = request.data.get('title', "")
            notification_body = request.data.get('body', "")
            send_notification_to_all_user = request.data.get('send_notification_to_all_user', False)
            organizations = request.data.get('organizations', [])
            if send_notification_to_all_user:
                organizations = []
                organization_queryset = Organization.objects.filter(
                    status=Status.ACTIVE
                ).order_by('pk')
                data_length = organization_queryset.count()
                chunk_size = 100
                number_of_operations = int((data_length / chunk_size) + 1)
                lower_limit = 0
                upper_limit = chunk_size
                for _ in range(0, number_of_operations):
                    data_limit = organization_queryset[lower_limit : upper_limit]
                    dict_ = data_limit.aggregate(Max('id'), Min('id'))
                    min_id = dict_.get('id__min', None)
                    max_id = dict_.get('id__max', None)
                    lower_limit = upper_limit
                    upper_limit += chunk_size
                    if min_id and max_id:
                        send_push_notification_to_mobile_app_by_org.delay(
                            org_ids=organizations,
                            title=notification_title,
                            body=notification_body,
                            data={},
                            entry_by_id=self.request.user.id,
                            min_id=min_id,
                            max_id=max_id
                        )
            else:
                send_push_notification_to_mobile_app_by_org.delay(
                    org_ids=organizations,
                    title=notification_title,
                    body=notification_body,
                    data={},
                    entry_by_id=self.request.user.id
                )
            response_content = {'message': 'Successfully Send Push Notification'}
            return Response(response_content, status=status.HTTP_201_CREATED)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class UserNotificationList(ListAPICustomView):
    permission_classes = (AnyLoggedInUser,)

    serializer_class = UserNotificationListSerializer

    def get_queryset(self):
        queryset = PushNotification.objects.filter(
            user__id=self.request.user.id
        ).order_by('-id')
        return queryset


class UserNotificationDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (AnyLoggedInUser,)

    serializer_class = UserNotificationDetailsSerializer
    lookup_field = 'alias'

    def get_queryset(self):
        queryset = PushNotification.objects.filter(
            user__organization=self.request.user.organization_id
        ).order_by('-id')
        return queryset


class NotificationCount(ListAPIView):
    available_permission_classes = (AnyLoggedInUser, )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        # Define a key for caching notification count data specific to the user
        cache_key = f"{NOTIFICATION_COUNT_USER_CACHE_KEY_PREFIX}{request.user.id}"

        # Retrieve cached notification count data
        notification_count_data = cache.get(key=cache_key)

        if notification_count_data is None:
            total = PushNotification.objects.filter(
                user__id=request.user.id
            ).only('pk')

            read = PushNotification.objects.filter(
                status=Status.INACTIVE,
                user__id=request.user.id
            ).only('pk')

            unread = PushNotification.objects.filter(
                status=Status.ACTIVE,
                user__id=request.user.id
            ).only('pk')

            total_count = total.count()
            read_count = read.count()
            unread_count = total_count - read_count

            notification_count_data = {
                'total': total_count,
                'read': read_count,
                'unread': unread_count
            }

            cache.set(
                key=cache_key,
                value=notification_count_data,
                timeout=timedelta(hours=24).total_seconds()
            )
            # Log the action of caching notification count data for the user
            logger.info(f"Cached notification count data for user id: {request.user.id}")
        else:
            # Log the action of retrieving notification count data from the cache
            logger.info(f"Retrieved notification count data from cache for user id: {request.user.id}")

        return Response(notification_count_data, status=status.HTTP_200_OK)


class MarkAllNotificationAsRead(APIView):
    available_permission_classes = (AnyLoggedInUser, )
    permission_classes = (CheckAnyPermission,)

    def post(self, request):

        notifications = PushNotification.objects.filter(
            status=Status.ACTIVE,
            user__id=request.user.id
        ).update(status=Status.INACTIVE)

        response = {
            'message': f'Successfully marked {notifications} notifications as read',
            'status': 'Success',
        }
        return Response(response, status=status.HTTP_200_OK)


class NotificationListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsTelemarketer,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = NotificationSerializer.List

    def get_queryset(self):
        queryset = Notification.objects.filter(
            status=Status.ACTIVE
        ).annotate(
            organizations=ArrayAgg(Cast('organizations_notification__organization__name', CharField())),
        ).order_by('-id')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        id_of_queryset = queryset.values_list('id', flat=True)
        response_data = self.get_from_cache(
            queryset=id_of_queryset,
            request=request,
        )

        return response_data

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            send_notification_to_all_user = request.data.get('send_notification_to_all_user', False)
            organizations = request.data.get('organizations', [])
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(entry_by_id=request.user.id)
            if serializer.instance.image:
                image_url = serializer.instance.image.thumbnail['1440x720'].url
                large_icon_url = serializer.instance.image.thumbnail['256x256'].url
            else:
                image_url = ""
                large_icon_url = ""
            title = serializer.instance.title
            body = serializer.instance.body
            data = serializer.instance.data
            url = serializer.instance.url
            if url is None or url == "":
                url = ""
            notification_id = serializer.instance.id
            if send_notification_to_all_user:
                organizations = []
                organization_queryset = Organization.objects.filter(
                    status=Status.ACTIVE
                ).order_by('pk')
                data_length = organization_queryset.count()
                chunk_size = 100
                number_of_operations = int((data_length / chunk_size) + 1)
                lower_limit = 0
                upper_limit = chunk_size
                for _ in range(0, number_of_operations):
                    data_limit = organization_queryset[lower_limit : upper_limit]
                    dict_ = data_limit.aggregate(Max('id'), Min('id'))
                    min_id = dict_.get('id__min', None)
                    max_id = dict_.get('id__max', None)
                    lower_limit = upper_limit
                    upper_limit += chunk_size
                    if min_id and max_id:
                        send_push_notification_to_mobile_app_by_org.delay(
                            org_ids=organizations,
                            notification_id=notification_id,
                            title=title,
                            body=body,
                            data=data,
                            url=url,
                            image=image_url,
                            large_icon=large_icon_url,
                            entry_by_id=self.request.user.id,
                            min_id=min_id,
                            max_id=max_id
                        )
            else:
                organizations = json.loads(organizations)
                send_push_notification_to_mobile_app_by_org.delay(
                    org_ids=organizations,
                    notification_id=notification_id,
                    title=title,
                    body=body,
                    data=data,
                    url=url,
                    image=image_url,
                    large_icon=large_icon_url,
                    entry_by_id=self.request.user.id
                )
            response_content = {'message': 'Successfully Send Notification'}
            return Response(response_content, status=status.HTTP_201_CREATED)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
