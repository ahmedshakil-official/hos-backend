from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from ..models import ProcureStatus

from core.enums import PersonGroupType
from procurement.enums import ProcureStatus as procure_status


# pylint: disable=old-style-class, no-init
class ProcureStatusMeta(ListSerializer.Meta):
    model = ProcureStatus
    fields = ListSerializer.Meta.fields + (
        'current_status',
        'procure',
        'remarks',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProcureStatusModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list/create ProcureStatus model
        '''

        # pylint: disable=old-style-class, no-init

        class Meta(ProcureStatusMeta):
            pass

    class Post(ListSerializer):
        '''
        This serializer will be used to list/create ProcureStatus model
        '''

        # pylint: disable=old-style-class, no-init

        class Meta(ProcureStatusMeta):
            pass

        def validate_procure(self, procure):
            user = self.context.get("request").user
            current_status = procure.current_status

            if procure.procure_group is not None:
                raise serializers.ValidationError(f"Procure already belongs to a group(#{procure.procure_group.id})")

            # validation for procure current status update by contractor
            if user.person_group == PersonGroupType.CONTRACTOR and (
                current_status != procure_status.PICKED
                or self.initial_data.get("current_status") != procure_status.DELIVERED
            ):
                raise serializers.ValidationError(
                    "Contractors can only change status from 'Picked' to 'Delivered'."
                )
            return procure
