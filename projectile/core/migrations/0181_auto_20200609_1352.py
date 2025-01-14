# Generated by Django 2.2.10 on 2020-06-09 07:52

import common.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0180_auto_20200608_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='license_image',
            field=common.fields.TimestampImageField(blank=True, null=True, upload_to='organization/license'),
        ),
        migrations.AddField(
            model_name='organization',
            name='license_no',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
