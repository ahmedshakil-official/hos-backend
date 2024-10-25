# Generated by Django 2.2.25 on 2022-01-07 09:44

import common.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pharmacy', '0151_purchase_invoice_group'),
        ('core', '0205_scriptfilestorage_date'),
        ('procurement', '0006_procure_requisition'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcureIssueLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateTimeField()),
                ('type', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Unavailability'), (2, 'Rate Discrepancy'), (3, 'Other')], db_index=True, default=3)),
                ('remarks', models.CharField(blank=True, max_length=512, null=True)),
                ('geo_location_data', common.fields.JSONTextField(blank=True, default='{}', null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_issue_employees', to='core.PersonOrganization')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='procurement_procureissuelog_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name')),
                ('prediction_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_issue_items', to='procurement.PredictionItem')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='stocks_procure_issue_items', to='pharmacy.Stock')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_issue_suppliers', to='core.PersonOrganization')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='procurement_procureissuelog_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name': 'Procure Issue',
                'verbose_name_plural': 'Procure Issues',
            },
        ),
    ]
