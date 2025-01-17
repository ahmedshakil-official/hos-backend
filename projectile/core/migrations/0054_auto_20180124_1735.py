# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-24 11:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0053_auto_20180124_1518'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonOrganizationSalary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_no', models.CharField(blank=True, max_length=32, null=True)),
                ('basic', models.FloatField(default=0.0)),
                ('office_provident_fund', models.FloatField(default=0.0)),
                ('person_provident_fund', models.FloatField(default=0.0)),
                ('premi_office', models.FloatField(default=0.0)),
                ('premi_personal', models.FloatField(default=0.0)),
                ('dps_office', models.FloatField(default=0.0)),
                ('dps_personal', models.FloatField(default=0.0)),
                ('special_allowance', models.FloatField(default=0.0)),
                ('income_tax', models.FloatField(default=0.0)),
                ('utility_bill', models.FloatField(default=0.0)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='core_personorganizationsalary_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('person_organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='persons_organization_salary', to='core.PersonOrganization')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='core_personorganizationsalary_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'verbose_name': 'Person Salary in Organization',
                'verbose_name_plural': 'Person Salary in Organizations',
            },
        ),
        migrations.AlterIndexTogether(
            name='personorganizationsalary',
            index_together=set([('organization', 'person_organization')]),
        ),
    ]
