from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer


from core.custom_serializer.person_organization import PersonOrganizationModelSerializer
# importing models
from core.models import EmployeeManager


class EmployeeManagerMeta(ListSerializer.Meta):
    model = EmployeeManager
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'status'
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()

## Employee Manager Serializer
# details
# list view

class EmployeeManagerModelSerializer:

    class List(ListSerializer):
        employee = PersonOrganizationModelSerializer.MinimalList()
        manager = PersonOrganizationModelSerializer.MinimalList()

        class Meta(EmployeeManagerMeta):
            fields = EmployeeManagerMeta.fields + (
                'employee',
                'manager'
            )

    class Details(ListSerializer):
        employee = PersonOrganizationModelSerializer.MinimalList()
        manager = PersonOrganizationModelSerializer.MinimalList()

        class Meta(EmployeeManagerMeta):
            fields = EmployeeManagerMeta.fields + (
                'employee',
                'manager'
            )
