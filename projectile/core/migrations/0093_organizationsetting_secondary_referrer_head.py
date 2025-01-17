# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-06 11:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0051_auto_20180626_0627'),
        ('core', '0092_auto_20180703_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='secondary_referrer_head',
            field=models.ForeignKey(blank=True, help_text='Choose a default Transaction head for paying to second referrer', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='referrer_transaction_head', to='account.TransactionHead'),
        ),
    ]
