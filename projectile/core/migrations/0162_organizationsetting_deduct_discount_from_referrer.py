# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-09-27 06:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0161_personorganization_referrer_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='deduct_discount_from_referrer',
            field=models.BooleanField(default=False, help_text='Settings for enable/disable deduct discount from referrer'),
        ),
    ]
