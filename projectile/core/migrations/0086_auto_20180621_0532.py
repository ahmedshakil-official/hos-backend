# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-21 05:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0085_organizationsetting_default_cashpoint'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='personorganization',
            unique_together=set([('person', 'organization', 'person_group', 'status')]),
        ),
    ]
