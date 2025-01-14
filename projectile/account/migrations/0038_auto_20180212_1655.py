# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-12 10:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0060_organizationsetting_trace_admission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0037_payabletoperson_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountCheque',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reference', models.CharField(blank=True, db_index=True, max_length=64, null=True, verbose_name=b'reference name')),
                ('condition', enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Used'), (2, b'Unused'), (3, b'Returned')], db_index=True, default=0, verbose_name=b'group of conditions')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_cheque', to='account.Accounts')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accountcheque_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accountcheque_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'verbose_name_plural': 'account cheques',
            },
        ),
        migrations.AlterIndexTogether(
            name='accountcheque',
            index_together=set([('organization', 'status', 'account')]),
        ),
    ]
