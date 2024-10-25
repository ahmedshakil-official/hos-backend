# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-29 10:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0059_auto_20180626_0627'),
        ('core', '0090_auto_20180626_0627'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinic', '0110_merge_20180626_1312'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceConsumedGroupSalesTransation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('transaction_group', models.CharField(blank=True, max_length=255, null=True, verbose_name='unique code for group transaction')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_serviceconsumedgroupsalestransation_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('sales', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales_for_service_consumed_group', to='pharmacy.Sales')),
                ('service_consumed_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='group_service_consumed', to='clinic.ServiceConsumedGroup')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_serviceconsumedgroupsalestransation_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'verbose_name_plural': 'ServiceConsumeds Sales Transation',
            },
        ),
    ]