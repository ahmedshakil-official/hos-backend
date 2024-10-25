# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-20 12:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0065_auto_20180313_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email',
            field=models.EmailField(db_index=True, default=None, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='organization',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization'),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone',
            field=models.CharField(db_index=True, default=None, max_length=24, null=True),
        ),
    ]
