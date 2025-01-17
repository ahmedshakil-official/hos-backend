# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-20 10:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0106_auto_20180919_1738'),
        ('clinic', '0127_auto_20180919_1738'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subservicereport',
            options={},
        ),
        migrations.AddField(
            model_name='subservicereport',
            name='clone',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.SubServiceReport'),
        ),
        migrations.AddField(
            model_name='subservicereport',
            name='is_global',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Private'), (1, b'Global'), (2, b'Changed into Global')], db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='subservicereport',
            name='organization',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
    ]
