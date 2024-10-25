# Generated by Django 5.0 on 2024-01-04 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0175_alter_product_order_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockiolog',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='stockiolog',
            name='person_organization_patient',
        ),
        migrations.AddField(
            model_name='purchase',
            name='customer_area_dynamic_discount_factor',
            field=models.DecimalField(decimal_places=3, default=0.0, help_text="The dynamic discount of a customer's area when the order is placed", max_digits=19),
        ),
        migrations.AddField(
            model_name='purchase',
            name='customer_dynamic_discount_factor',
            field=models.DecimalField(decimal_places=3, default=0.0, help_text='The dynamic discount of a customer org when the order is placed', max_digits=19),
        ),
        migrations.AddField(
            model_name='purchase',
            name='dynamic_discount_amount',
            field=models.DecimalField(decimal_places=3, default=0.0, help_text='The additional discount amount customer get for dynamic discount', max_digits=19),
        ),
        migrations.AddField(
            model_name='stockiolog',
            name='base_discount',
            field=models.DecimalField(decimal_places=3, default=0.0, help_text='The discount rate from product before adding dynamic discount', max_digits=19),
        ),
    ]