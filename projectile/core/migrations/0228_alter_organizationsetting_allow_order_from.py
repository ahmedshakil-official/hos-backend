# Generated by Django 5.0 on 2023-12-29 09:26

import enumerify.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0227_passwordreset_reset_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationsetting',
            name='allow_order_from',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Only Stock'), (2, 'Stock and Next Day'), (3, 'Open'), (4, 'Stock and Open')], db_index=True, default=3, help_text='Choices for product order from for ecommerce'),
        ),
    ]
