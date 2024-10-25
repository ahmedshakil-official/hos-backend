# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-24 10:26
from __future__ import unicode_literals

from django.db import migrations, models
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0096_subservicereportfield_show_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='sub_type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Others')], db_index=True, default=1),
        ),
        migrations.AddField(
            model_name='subservice',
            name='code_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='subservice',
            name='image_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='subservice',
            name='processing_time',
            field=models.PositiveIntegerField(default=0, help_text='This field will store processing time in minute.'),
        ),
    ]
