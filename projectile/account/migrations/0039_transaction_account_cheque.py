# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-14 14:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0038_auto_20180212_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='account_cheque',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='accoun_cheque_of', to='account.AccountCheque', verbose_name=b'account cheque'),
        ),
    ]