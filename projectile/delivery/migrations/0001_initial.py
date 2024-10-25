# Generated by Django 2.2.20 on 2021-04-20 08:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0193_auto_20210303_1118'),
        ('pharmacy', '0143_auto_20210413_0140'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('amount', models.FloatField(default=0.0)),
                ('discount', models.FloatField(default=0.0)),
                ('discount_rate', models.FloatField(default=0.0)),
                ('round_discount', models.FloatField(default=0.0)),
                ('vat_rate', models.FloatField(default=0.0)),
                ('vat_total', models.FloatField(default=0.0)),
                ('tax_rate', models.FloatField(default=0.0)),
                ('tax_total', models.FloatField(default=0.0)),
                ('grand_total', models.FloatField(default=0.0)),
                ('delivery_charge', models.FloatField(default=0.0)),
                ('tracking_status', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Pending'), (2, 'Accepted'), (3, 'Ready to Deliver'), (4, 'On the Way'), (5, 'Delivered'), (6, 'Completed'), (7, 'Rejected'), (8, 'Cancelled'), (9, 'Partial Delivered'), (10, 'Full Returned')], db_index=True, default=3)),
                ('assigned_by', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_assigned_by', to='core.PersonOrganization', verbose_name='Assigned to a delivery man')),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_assigned_to', to='core.PersonOrganization', verbose_name='Person responsible for a delivery')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_delivery_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('order_by_organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='organization_order_by', to='core.Organization')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderDeliveryConnector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('delivery', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='delivery.Delivery')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_orderdeliveryconnector_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='pharmacy.Purchase')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_orderdeliveryconnector_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='delivery',
            name='orders',
            field=models.ManyToManyField(related_name='delivery_orders', through='delivery.OrderDeliveryConnector', to='pharmacy.Purchase'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_delivery_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.CreateModel(
            name='StockDelivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('product_name', models.CharField(max_length=512)),
                ('quantity', models.FloatField(default=0.0)),
                ('rate', models.FloatField(default=0.0)),
                ('batch', models.CharField(max_length=128)),
                ('expire_date', models.DateField(blank=True, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('discount_rate', models.FloatField(default=0.0)),
                ('discount_total', models.FloatField(default=0.0)),
                ('vat_rate', models.FloatField(default=0.0)),
                ('vat_total', models.FloatField(default=0.0)),
                ('tax_rate', models.FloatField(default=0.0)),
                ('tax_total', models.FloatField(default=0.0)),
                ('unit', models.CharField(max_length=56)),
                ('round_discount', models.FloatField(default=0.0, help_text="discount amount distributed by inventory's round_discount")),
                ('tracking_status', enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Pending'), (2, 'Accepted'), (3, 'Ready to Deliver'), (4, 'On the Way'), (5, 'Delivered'), (6, 'Completed'), (7, 'Rejected'), (8, 'Cancelled'), (9, 'Partial Delivered'), (10, 'Full Returned')], db_index=True, default=1)),
                ('delivery', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='delivery.Delivery')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_stockdelivery_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='products', to='pharmacy.Purchase')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='stocks_delivery', to='pharmacy.Stock')),
                ('stock_io', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='stock_io_delivery', to='pharmacy.StockIOLog')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_stockdelivery_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
                'index_together': {('organization', 'status')},
            },
        ),
        migrations.AlterIndexTogether(
            name='delivery',
            index_together={('organization', 'status')},
        ),
    ]