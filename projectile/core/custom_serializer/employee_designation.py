from rest_framework.serializers import ValidationError
from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.validators import (
    validate_uniq_designation_with_org
)
from ..models import (
    EmployeeDesignation
)


class EmployeeDesignationMeta(ListSerializer.Meta):
    # pylint: disable=old-style-class, no-init
    model = EmployeeDesignation
    fields = ListSerializer.Meta.fields + (
        'name',
        'description',
        'department',
    )

# pylint: disable=old-style-class, no-init
class EmployeeDesignationModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list EmployeeDesignation model
        '''
        class Meta(EmployeeDesignationMeta):
            pass

        def validate_name(self, value):
            if validate_uniq_designation_with_org(self, value, EmployeeDesignation):
                return value
            else:
                raise ValidationError(
                    'YOU_HAVE_ALREADY_A_DESIGNATION_WITH_SAME_NAME_AND_DEPARTMENT')

    class Details(ListSerializer):
        '''
        This serializer will be used to see details of EmployeeDesignation model
        '''
        from core.serializers import (
            DepartmentSerializer
        )
        department = DepartmentSerializer()
        class Meta(EmployeeDesignationMeta):
            pass
