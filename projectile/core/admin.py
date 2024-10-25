from django.contrib import admin
from common.admin import (
    CreatedAtUpdatedAtBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganizationAdmin,
    NameSlugDescriptionBaseModelAdmin,
    NameSlugDescriptionBaseOrganizationWiseModelAdmin,
)

from .models import (
    Person,
    Department,
    EmployeeDesignation,
    Organization,
    OrganizationSetting,
    PersonOrganization,
    GroupPermission,
    PersonOrganizationGroupPermission,
    SmsLog,
    ScriptFileStorage,
    Issue,
    IssueStatus,
    AuthLog,
    EmployeeManager,
    DeliveryHub,
    PasswordReset,
    OTP,
    Area,
)


class PersonOrganizationInline(admin.TabularInline):
    model = PersonOrganization
    fk_name = 'person'
    fields = ('organization', 'status', 'person_group')
    extra = 0
    show_change_link = True
    can_delete = False
    raw_id_fields = (
        'organization',
    )

class PersonAdmin(CreatedAtUpdatedAtBaseModel):
    inlines = [PersonOrganizationInline,]
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        '_person', 'code', 'gender', 'nid', 'balance',
        'joining_date', 'person_group', '_designation', 'organization'
    )

    def _person(self, obj):
        if obj.company_name:
            return u'{} - {}'.format(obj.company_name, obj.contact_person_number)
        return obj.get_full_name()

    def _designation(self, obj):
        if obj.designation:
            return u'{}'.format(obj.designation.name)
        return None

    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'organization', 'person_group',
        'gender',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'first_name', 'last_name', 'phone',
        'email', 'code', 'nid',
        'company_name', 'contact_person',
        'contact_person_number'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'designation',
        'belongs_to',
        'organization',
    )


admin.site.register(Person, PersonAdmin)


class PersonOrganizationAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'person', 'balance',
        'person_group'
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'person_group',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'person__first_name', 'person__last_name',
        'person__code', 'person__phone',
        'alias'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'person', 'designation',
        # 'referrer_category',
    )


admin.site.register(PersonOrganization, PersonOrganizationAdmin)


class GroupPermissionAdmin(NameSlugDescriptionBaseModelAdmin):
    list_display = NameSlugDescriptionBaseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseModelAdmin.raw_id_fields

admin.site.register(GroupPermission, GroupPermissionAdmin)


class PersonOrganizationGroupPermissionAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        '_person', 'permission',
        '_organization',
    )

    def _person(self, obj):
        return obj.person_organization.person.get_full_name()

    def _organization(self, obj):
        return obj.person_organization.organization.name

    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'person_organization__organization',
        'permission'
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'person_organization__person__first_name',
        'person_organization__person__last_name',
        'person_organization__person__phone',
        'permission__name',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'person_organization',
        'permission'
    )


admin.site.register(PersonOrganizationGroupPermission, PersonOrganizationGroupPermissionAdmin)


class DepartmentAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields +('clone',)


admin.site.register(Department, DepartmentAdmin)


class EmployeeDesignationAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    # department, designation
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + (
        '_department',
    )

    def _department(self, obj):
        if obj.department:
            return obj.department.name
        return None

    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields + (
        'department__name',
    )
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + (
        'clone', 'department'
    )


admin.site.register(EmployeeDesignation, EmployeeDesignationAdmin)


class OrganizationSettingAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'organization', 'date_format',
        'order_ending_time',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'organization',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + ('organization__name',)
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'organization',
    )

admin.site.register(OrganizationSetting, OrganizationSettingAdmin)


class OrganizationAdmin(NameSlugDescriptionBaseModelAdmin):
    list_display = NameSlugDescriptionBaseModelAdmin.list_display + (
        'type', 'address', 'primary_mobile',
        'other_contact', 'contact_person', 'contact_person_designation',
        'email', 'delivery_thana', 'min_order_amount',
    )

    list_filter = NameSlugDescriptionBaseModelAdmin.list_filter + ('type',)
    search_fields = NameSlugDescriptionBaseModelAdmin.search_fields + (
        'primary_mobile', 'contact_person',
        'email', 'delivery_thana',
    )
    raw_id_fields = NameSlugDescriptionBaseModelAdmin.raw_id_fields


admin.site.register(Organization, OrganizationAdmin)


class SmsLogAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass
admin.site.register(SmsLog, SmsLogAdmin)

class ScriptFileStorageAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'content', 'content_type', 'purpose',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'content_type',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'name', 'content_type', 'alias',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'entry_by', 'updated_by'
    )

admin.site.register(ScriptFileStorage, ScriptFileStorageAdmin)


class IssueAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(Issue, IssueAdmin)


class IssueStatusAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(IssueStatus, IssueStatusAdmin)


class AuthLogAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(AuthLog, AuthLogAdmin)

class EmployeeManagerAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(EmployeeManager, EmployeeManagerAdmin)


class DeliveryHubAdmin(NameSlugDescriptionBaseModelAdmin):
    pass

admin.site.register(DeliveryHub, DeliveryHubAdmin)


class OTPAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(OTP, OTPAdmin)


class PasswordResetAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    pass

admin.site.register(PasswordReset, PasswordResetAdmin)


class AreaAdmin(NameSlugDescriptionBaseModelAdmin):
    pass


admin.site.register(Area, AreaAdmin)
