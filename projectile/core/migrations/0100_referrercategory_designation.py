# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-10 06:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0099_organizationsetting_print_test_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='referrercategory',
            name='designation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='referrer_category_designation', to='core.EmployeeDesignation'),
        ),
    ]
