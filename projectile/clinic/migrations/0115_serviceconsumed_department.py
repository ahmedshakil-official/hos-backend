# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-07 11:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0114_organizationdepartment'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumeds', to='clinic.OrganizationDepartment'),
        ),
    ]
