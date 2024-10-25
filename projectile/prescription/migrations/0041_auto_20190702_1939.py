# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-02 13:39
from __future__ import unicode_literals

import autoslug.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0147_auto_20190625_1826'),
        ('prescription', '0040_auto_20190527_1036'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrescriptionAdditionalInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('slug', autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_global', enumerify.fields.SelectIntegerField(choices=[(0, b'Private'), (1, b'Global'), (2, b'Changed into Global')], db_index=True, default=0)),
                ('clone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='prescription.PrescriptionAdditionalInfo')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescription_prescriptionadditionalinfo_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescription_prescriptionadditionalinfo_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='PrescriptionExtraInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('info', models.CharField(blank=True, max_length=512, null=True)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescription_prescriptionextrainfo_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('prescription', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescriptionextrainfo_list', to='prescription.Prescription')),
                ('relative', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='prescription.PrescriptionAdditionalInfo')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescription_prescriptionextrainfo_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
        ),
        migrations.AlterField(
            model_name='prescriptionsymptom',
            name='prescription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescriptionsymptom_list', to='prescription.Prescription'),
        ),
        migrations.AddField(
            model_name='prescription',
            name='prescription_additional_info',
            field=models.ManyToManyField(through='prescription.PrescriptionExtraInfo', to='prescription.PrescriptionAdditionalInfo'),
        ),
        migrations.AlterUniqueTogether(
            name='prescriptionextrainfo',
            unique_together=set([('prescription', 'relative')]),
        ),
        migrations.AlterIndexTogether(
            name='prescriptionextrainfo',
            index_together=set([('prescription', 'relative')]),
        ),
    ]
