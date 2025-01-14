# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-27 09:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0067_auto_20180323_1311'),
        ('pharmacy', '0046_purchase_purchase_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeaccountaccess',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='accounts_access_person_organization', to='core.PersonOrganization', verbose_name='employee in person organization'),
        ),
        migrations.AddField(
            model_name='employeestorepointaccess',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='storepoint_access_person_organization', to='core.PersonOrganization', verbose_name='employee in person organization'),
        ),
        migrations.AddField(
            model_name='purchase',
            name='person_organization_receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='purchase_receiver_person_organization', to='core.PersonOrganization', verbose_name='receiver in person organization'),
        ),
        migrations.AddField(
            model_name='purchase',
            name='person_organization_supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='purchase_supplier_person_organization', to='core.PersonOrganization', verbose_name='supplier in person organization'),
        ),
        migrations.AddField(
            model_name='sales',
            name='person_organization_buyer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='buyer_patient_person_organization', to='core.PersonOrganization', verbose_name='buyer in person organization'),
        ),
        migrations.AddField(
            model_name='sales',
            name='person_organization_salesman',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='salesman_patient_person_organization', to='core.PersonOrganization', verbose_name='salesman in person organization'),
        ),
        migrations.AddField(
            model_name='stockadjustment',
            name='person_organization_employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='stockadjustment_employee_person_organization', to='core.PersonOrganization', verbose_name='stock adjustment employee in person organization'),
        ),
        migrations.AddField(
            model_name='stockadjustment',
            name='person_organization_patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='stockadjustment_patient_person_organization', to='core.PersonOrganization', verbose_name='stock adjustment patient in person organization'),
        ),
        migrations.AddField(
            model_name='stockiolog',
            name='person_organization_patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='stock_io_log_patient_person_organization', to='core.PersonOrganization', verbose_name='io log paitent in person organization'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='person_organization_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transfer_by_person_organization', to='core.PersonOrganization', verbose_name='transfer by in person organization'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='person_organization_received_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transfer_received_by_person_organization', to='core.PersonOrganization', verbose_name='transfer received by in person organization'),
        ),
    ]
