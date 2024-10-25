# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-20 13:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0057_admissionconsultant'),
        ('core', '0040_auto_20171219_1709'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='default_subservice',
            field=models.ForeignKey(blank=True, help_text='select sub-service', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.SubService'),
        ),
    ]
