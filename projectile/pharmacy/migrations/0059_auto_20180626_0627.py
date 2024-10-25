# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-26 06:27
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0058_auto_20180619_0847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='productform',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='productgeneric',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='productgroup',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='productmanufacturingcompany',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='productsubgroup',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='storepoint',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
    ]