# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-07 10:15
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_organizationsetting_admission_head'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='patient_code_length',
            field=models.PositiveIntegerField(default=9, validators=[django.core.validators.MaxValueValidator(16)]),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='patient_code_prefix',
            field=models.CharField(default=b'OMIS', max_length=10),
        ),
    ]
