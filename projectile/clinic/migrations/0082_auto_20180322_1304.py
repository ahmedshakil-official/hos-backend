# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-22 07:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0081_auto_20180321_1233'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='investigationfield',
            options={'ordering': ('-priority',), 'verbose_name': 'Investigation Field'},
        ),
        migrations.AlterModelOptions(
            name='reportfieldcategory',
            options={'ordering': ('-priority',), 'verbose_name_plural': 'Report Field Categories'},
        ),
        migrations.AddField(
            model_name='investigationfield',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='Highest comes first.'),
        ),
        migrations.AddField(
            model_name='reportfieldcategory',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='Highest comes first.'),
        ),
    ]
