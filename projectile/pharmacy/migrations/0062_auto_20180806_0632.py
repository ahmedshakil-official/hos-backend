# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-06 06:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0114_organizationdepartment'),
        ('pharmacy', '0061_merge_20180711_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='organization_department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='purchases', to='clinic.OrganizationDepartment'),
        ),
        migrations.AddField(
            model_name='sales',
            name='organization_department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales', to='clinic.OrganizationDepartment'),
        ),
    ]
