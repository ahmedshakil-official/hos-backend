# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-02 11:10
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0140_organizationsetting_allow_default_discount_vat_rate'),
        ('pharmacy', '0102_sales_sales_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationWiseDiscardedProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('entry_type', enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Edit'), (2, b'Merge'), (3, b'Other')], db_index=True, default=1)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='pharmacy_organizationwisediscardedproduct_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='organization_wise_discarded_parent_product', to='pharmacy.Product')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='organization_wise_discarded_product', to='pharmacy.Product')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='pharmacy_organizationwisediscardedproduct_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'verbose_name_plural': "Organization's Discarded Product",
            },
        ),
        migrations.AlterIndexTogether(
            name='organizationwisediscardedproduct',
            index_together=set([('organization', 'product')]),
        ),
    ]
