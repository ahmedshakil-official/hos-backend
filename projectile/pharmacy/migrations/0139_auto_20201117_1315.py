# Generated by Django 2.2.13 on 2020-11-17 07:15

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0138_purchase_system_platform'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordertracking',
            name='order_status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Pending'), (2, 'Accepted'), (3, 'Ready to Deliver'), (4, 'On the Way'), (5, 'Delivered'), (6, 'Completed'), (7, 'Rejected'), (8, 'Cancelled'), (9, 'Partial Delivered'), (10, 'Full Returned')], db_index=True, default=1, help_text='Define current status of order'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='current_order_status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Pending'), (2, 'Accepted'), (3, 'Ready to Deliver'), (4, 'On the Way'), (5, 'Delivered'), (6, 'Completed'), (7, 'Rejected'), (8, 'Cancelled'), (9, 'Partial Delivered'), (10, 'Full Returned')], db_index=True, default=1, help_text='Define current status of order'),
        ),
    ]
