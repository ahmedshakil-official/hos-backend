# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-21 08:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0060_auto_20190116_0536'),
        ('core', '0126_auto_20190116_0536'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='sales_return_head',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales_return_transaction_head', to='account.TransactionHead'),
        ),
    ]