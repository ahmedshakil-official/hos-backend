from rest_framework import serializers
from rest_framework.serializers import (
    ValidationError
)

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from core.models import Issue, IssueStatus
from .person_organization import PersonOrganizationModelSerializer
from .organization import OrganizationModelSerializer
from .person import PersonModelSerializer
from .issue_status import IssueStatusModelSerializer


class IssueMeta(ListSerializer.Meta):
    model = Issue
    fields = ListSerializer.Meta.fields + (
        'date',
        'type',
        'current_issue_status',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class IssueModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to get data of Issue
        '''
        reported_to = PersonOrganizationModelSerializer.MinimalList()
        reported_against = PersonOrganizationModelSerializer.MinimalList()
        responsible_to_resolve = PersonOrganizationModelSerializer.MinimalList()
        issue_organization = OrganizationModelSerializer.LiteWithEntryBy()
        entry_by = PersonModelSerializer.EntryBy(read_only=True)

        class Meta(IssueMeta):
            fields = IssueMeta.fields + (
                'order',
                'invoice_group',
                'entry_by',
                'reported_to',
                'reported_against',
                'responsible_to_resolve',
                'issue_organization',
                'remarks',
            )

    class Post(ListSerializer):
        '''
        This serializer will be used to post data of Issue
        '''
        class Meta(IssueMeta):
            fields = IssueMeta.fields + (
                'order',
                'invoice_group',
                'reported_to',
                'reported_against',
                'responsible_to_resolve',
                'issue_organization',
                'remarks',
            )

        def create(self, validated_data):
            request = self.context.get("request")
            issue = Issue.objects.create(
                **validated_data
            )
            issue.save()
            # Create issue status instance
            if issue:
                issue_status = IssueStatus.objects.create(
                    issue_id=issue.id,
                    entry_by_id=request.user.id
                )
                issue_status.save()

            return issue


    class Details(ListSerializer):
        '''
        This serializer will be used to get data of Issue
        '''
        reported_to = PersonOrganizationModelSerializer.MinimalList()
        reported_against = PersonOrganizationModelSerializer.MinimalList()
        responsible_to_resolve = PersonOrganizationModelSerializer.MinimalList()
        issue_organization = OrganizationModelSerializer.LiteWithEntryBy()
        entry_by = PersonModelSerializer.EntryBy(read_only=True)
        issue_status = IssueStatusModelSerializer.Details(read_only=True, many=True)

        class Meta(IssueMeta):
            fields = IssueMeta.fields + (
                'order',
                'invoice_group',
                'entry_by',
                'reported_to',
                'reported_against',
                'responsible_to_resolve',
                'issue_organization',
                'remarks',
                'issue_status',
            )