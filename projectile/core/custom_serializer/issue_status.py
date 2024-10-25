from rest_framework import serializers
from rest_framework.serializers import (
    ValidationError
)

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from core.models import IssueStatus
from .person import PersonModelSerializer


class IssueStatusMeta(ListSerializer.Meta):
    model = IssueStatus
    fields = ListSerializer.Meta.fields + (
        'date',
        'issue',
        'issue_status',
        'remarks',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class IssueStatusModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to get data of         This serializer will be used to post data of IssueStatus

        '''
        class Meta(IssueStatusMeta):
            fields = IssueStatusMeta.fields + ()

    class Post(ListSerializer):
        '''
        This serializer will be used to post data of IssueStatus
        '''
        class Meta(IssueStatusMeta):
            fields = IssueStatusMeta.fields + ()


    class Details(ListSerializer):
        '''
        This serializer will be used to get details data of IssueStatus
        '''
        entry_by = PersonModelSerializer.EntryBy(read_only=True)


        class Meta(IssueStatusMeta):
            fields = IssueStatusMeta.fields + (
                'entry_by',
            )
