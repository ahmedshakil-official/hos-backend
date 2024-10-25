# Generated by Django 2.2.25 on 2022-03-31 04:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('procurement', '0010_auto_20220325_1213'),
    ]

    operations = [
        migrations.AddField(
            model_name='procure',
            name='current_status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Draft'), (2, 'Order Placed'), (3, 'Picked'), (4, 'Delivered'), (5, 'Paid'), (6, 'Completed')], db_index=True, default=1, help_text='Define current status of procure'),
        ),
        migrations.AddField(
            model_name='procure',
            name='estimated_collection_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ProcureStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateTimeField(auto_now_add=True, help_text='Date time for status changed')),
                ('current_status', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Draft'), (2, 'Order Placed'), (3, 'Picked'), (4, 'Delivered'), (5, 'Paid'), (6, 'Completed')], db_index=True, default=1, help_text='Define current status of procure')),
                ('remarks', models.CharField(blank=True, max_length=512, null=True)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='procurement_procurestatus_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('procure', models.ForeignKey(help_text='The procure for tracking status', on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_status', to='procurement.Procure')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='procurement_procurestatus_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name': 'Procure Status',
                'verbose_name_plural': 'Procure Statuses',
            },
        ),
    ]