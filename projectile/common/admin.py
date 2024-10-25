from django.contrib import admin
from reversion.admin import VersionAdmin


class CreatedAtUpdatedAtBaseModel(VersionAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [
            field.attname for field in model._meta.fields]
        super(CreatedAtUpdatedAtBaseModel, self).__init__(model, admin_site)

        # select fields those are foreign key
        # self.list_select_related = [
        #     field.name for field in model._meta.fields if field.is_relation]
        # super(CreatedAtUpdatedAtBaseModel, self).__init__(model, admin_site)

        # select fields those are foreign key
        self.raw_id_fields = [
            field.name for field in model._meta.fields if field.is_relation]
        super(CreatedAtUpdatedAtBaseModel, self).__init__(model, admin_site)

    # list_display = (
    #     'id',
    #     'status',
    #     'user_ip',
    # )

    list_filter = ('status',)
    search_fields = ('user_ip',)
    # raw_id_fields = ('entry_by', 'updated_by',)
    show_full_result_count = False


class CreatedAtUpdatedAtBaseModelWithOrganizationAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'organization',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'organization',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'organization__name',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'organization',
    )


class NameSlugDescriptionBaseModelAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'name',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'name',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields


class NameSlugDescriptionBaseOrganizationWiseModelAdmin(NameSlugDescriptionBaseModelAdmin):
    list_display = NameSlugDescriptionBaseModelAdmin.list_display + (
        'is_global',
        'organization',
    )
    list_filter = NameSlugDescriptionBaseModelAdmin.list_filter + (
        'organization',
        'is_global',
    )
    search_fields = NameSlugDescriptionBaseModelAdmin.search_fields + (
        'organization__name',
    )
    raw_id_fields = NameSlugDescriptionBaseModelAdmin.raw_id_fields + (
        'organization',
    )

