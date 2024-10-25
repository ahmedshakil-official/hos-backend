# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-06 07:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0128_auto_20190201_1301'),
        ('clinic', '0134_auto_20190201_1334'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeBedSectionAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('access_status', models.BooleanField(default=False)),
                ('bed_section', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='employee_section', to='clinic.BedSection')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='section_access_employee', to=settings.AUTH_USER_MODEL)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_employeebedsectionaccess_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('person_organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='section_access_person_organization', to='core.PersonOrganization', verbose_name='employee in person organization')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_employeebedsectionaccess_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'verbose_name': 'Employee Bed Section Access',
                'verbose_name_plural': 'Employee Bed Section Accesses',
            },
        ),
    ]
