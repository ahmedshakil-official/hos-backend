# Generated by Django 4.2.4 on 2023-10-12 11:41

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0170_productchangeslogs_order_limit_per_day_mirpur_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='logo',
            field=common.fields.TimestampVersatileImageField(blank=True, null=True, upload_to='logo/images'),
        ),
    ]
