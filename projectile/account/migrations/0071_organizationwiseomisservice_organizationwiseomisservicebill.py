# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-04 10:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0163_personorganization_area'),
        ('account', '0070_auto_20190828_0737'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationWiseOmisService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('service', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Installation'), (2, 'Data Entry'), (3, 'Training'), (4, 'Monthly Service Charge'), (5, 'Custom Services')], db_index=True, default=1, verbose_name='type of service')),
                ('kind', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'One Time'), (2, 'Limited Time'), (3, 'Periodic')], db_index=True, default=1, verbose_name='nature of service')),
                ('amount', models.FloatField(default=0)),
                ('billing_frequency', models.SmallIntegerField(default=0)),
                ('start_date', models.DateTimeField()),
                ('description', models.TextField(blank=True)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwiseomisservice_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwiseomisservice_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name': 'Organization-wise Service',
                'verbose_name_plural': 'Organization-wise Service',
            },
        ),
        migrations.CreateModel(
            name='OrganizationWiseOmisServiceBill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('billing_date', models.DateTimeField()),
                ('amount', models.FloatField(default=0)),
                ('paid_amount', models.FloatField(default=0)),
                ('discount_amount', models.FloatField(default=0)),
                ('is_published', models.BooleanField(default=False)),
                ('is_closed', models.BooleanField(default=False)),
                ('due_date', models.DateTimeField()),
                ('billing_cycle_on', models.BooleanField(default=False)),
                ('next_date', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('bill_for_service', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='omis_bill_for_services', to='account.OrganizationWiseOmisService')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwiseomisservicebill_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('next_bill', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='next_omis_bill', to='account.OrganizationWiseOmisServiceBill')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name')),
                ('previous_bill', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='previous_omis_bill', to='account.OrganizationWiseOmisServiceBill')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwiseomisservicebill_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name': 'Organizationwise Bill',
                'verbose_name_plural': 'Organizationwise Bills',
            },
        ),
    ]