# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-05 10:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0137_personorganization_salary_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganizationdiscount',
            name='person_organization_discount_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='person_organization_discount_by', to='core.PersonOrganization'),
        ),
        migrations.AddField(
            model_name='personorganizationdiscount',
            name='person_organization_on_request_of',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='person_organization_on_request_discount', to='core.PersonOrganization'),
        ),
    ]
