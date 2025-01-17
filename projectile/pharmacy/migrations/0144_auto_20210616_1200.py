# Generated by Django 2.2.20 on 2021-06-16 06:00

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0143_auto_20210413_0140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=common.fields.TimestampVersatileImageField(blank=True, null=True, upload_to='product/images'),
        ),
    ]
