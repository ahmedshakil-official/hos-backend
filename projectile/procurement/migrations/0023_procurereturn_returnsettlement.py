# Generated by Django 4.2.4 on 2023-10-05 12:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0219_otp_passwordreset'),
        ('pharmacy', '0170_productchangeslogs_order_limit_per_day_mirpur_and_more'),
        ('procurement', '0022_procure_contractor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcureReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateField()),
                ('reason', models.CharField(blank=True, choices=[('BROKEN_PRODUCT', 'Broken Product'), ('EXPIRED_PRODUCT', 'Expired Product'), ('WRONG_PRODUCT', 'Wrong Product'), ('OTHER', 'Other')], default='OTHER', max_length=20)),
                ('reason_note', models.CharField(blank=True, max_length=250)),
                ('product_name', models.CharField(blank=True, max_length=255)),
                ('total_return_amount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('total_settled_amount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('current_status', models.CharField(blank=True, choices=[('PENDING', 'Pending'), ('PARTIALLY_SETTLED', 'Partially Settled'), ('SETTLED', 'Settled')], default='PENDING', max_length=20)),
                ('settlement_method', models.CharField(blank=True, choices=[('CASH', 'Cash'), ('CHEQUE', 'Cheque'), ('NET_AGAINST_COMMISSION', 'Net Against Commission'), ('PRODUCT_REPLACEMENT', 'Product Replacement')], default='CASH', max_length=30)),
                ('full_settlement_date', models.DateTimeField(blank=True, null=True)),
                ('quantity', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('rate', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('contractor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractor_procure_returns', to='core.personorganization')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='employee_procure_returns', to='core.personorganization')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.organization', verbose_name='organization name')),
                ('procure', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_returns', to='procurement.procure')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='stock_procure_returns', to='pharmacy.stock')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name_plural': 'Procure Returns',
            },
        ),
        migrations.CreateModel(
            name='ReturnSettlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateTimeField()),
                ('settlement_method', models.CharField(blank=True, choices=[('CASH', 'Cash'), ('CHEQUE', 'Cheque'), ('NET_AGAINST_COMMISSION', 'Net Against Commission'), ('PRODUCT_REPLACEMENT', 'Product Replacement')], default='CASH', max_length=30)),
                ('settlement_method_reference', models.CharField(blank=True, max_length=250)),
                ('amount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='employee_return_settlements', to='core.personorganization')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('procure_return', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='procure_return_settlements', to='procurement.procurereturn')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name_plural': 'Procure Return Settlements',
            },
        ),
    ]