# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-26 09:59
from __future__ import unicode_literals

import common.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0056_organizationsetting_appointment_bulk_sms'),
        ('account', '0034_transaction_person_organization'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayableToPerson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('amount', models.FloatField(validators=[common.validators.validate_non_zero_amount])),
                ('group_id', models.CharField(blank=True, editable=False, max_length=255, null=True, verbose_name=b'unique code for group payable')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_payabletoperson_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payable_person', to=settings.AUTH_USER_MODEL)),
                ('person_organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payable_person_organization', to='core.PersonOrganization', verbose_name=b'person organization')),
                ('transaction_head', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payable_transaction_head', to='account.TransactionHead', verbose_name=b'transaction head')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_payabletoperson_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.AlterIndexTogether(
            name='payabletoperson',
            index_together=set([('organization', 'status')]),
        ),
    ]