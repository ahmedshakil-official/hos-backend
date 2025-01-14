# Generated by Django 2.2.24 on 2021-08-26 06:37

import common.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0008_auto_20200225_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='popupmessage',
            name='image',
            field=common.fields.TimestampVersatileImageField(blank=True, null=True, upload_to='banner/images'),
        ),
        migrations.AlterField(
            model_name='popupmessage',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
