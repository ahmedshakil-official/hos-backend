# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-10 10:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20171010_1631'),
        ('clinic', '0032_merge_20171010_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='subservicereportfield',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='bed',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='dutyshift',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='service',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='subservice',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='treatmentsession',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
    ]
