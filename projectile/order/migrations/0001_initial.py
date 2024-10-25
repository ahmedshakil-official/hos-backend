# Generated by Django 4.2.2 on 2023-12-07 07:39

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_json_field_schema_validator.validators
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0227_passwordreset_reset_date'),
        ('pharmacy', '0174_purchase_is_delayed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('date', models.DateTimeField()),
                ('delivery_date', models.DateTimeField(blank=True, null=True)),
                ('is_pre_order', models.BooleanField(default=False, help_text='Defines pre order / regular order cart')),
                ('sub_total', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('discount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('round', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('grand_total', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.organization', verbose_name='organization name')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
                'index_together': {('organization', 'status')},
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('stock_alias', models.UUIDField(blank=True, editable=False, help_text='The stock alias associated with this cart item.', null=True)),
                ('product_name', models.CharField(help_text='It contain full name of product, fullname=form+name+strength', max_length=255)),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('discount_rate', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('discount_amount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('total_amount', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('product_image', models.JSONField(blank=True, help_text='Product image data in JSON format', null=True, validators=[django_json_field_schema_validator.validators.JSONFieldSchemaValidator({'properties': {'full_size': {'format': 'uri', 'type': 'string'}, 'large': {'format': 'uri', 'type': 'string'}, 'small': {'format': 'uri', 'type': 'string'}}, 'required': ['full_size', 'small', 'large'], 'type': 'object'})])),
                ('mrp', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('price', models.DecimalField(decimal_places=3, default=0.0, max_digits=19)),
                ('company_name', models.CharField(max_length=255)),
                ('cart', models.ForeignKey(help_text='The cart to which this item belongs.', on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='order.cart')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.organization', verbose_name='organization name')),
                ('stock', models.ForeignKey(help_text='The stock associated with this cart item.', on_delete=django.db.models.deletion.DO_NOTHING, related_name='cart_item_stocks', to='pharmacy.stock')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
                'index_together': {('organization', 'status')},
            },
        ),
    ]