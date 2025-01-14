# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-28 07:37
from __future__ import unicode_literals

import autoslug.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0069_auto_20190725_1436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountcheque',
            name='condition',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Used'), (2, 'Unused'), (3, 'Returned')], db_index=True, default=0, verbose_name='group of conditions'),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accountcheque_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='reference_name',
            field=models.CharField(blank=True, db_index=True, default=None, max_length=64, null=True, verbose_name='reference name'),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='accountcheque',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accountcheque_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='ac_no',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='a/c number'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='bank',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='bank name'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='branch',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='branch of bank'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accounts_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='is_global',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Private'), (1, 'Global'), (2, 'Changed into Global')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Cash'), (2, 'Bank')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='accounts',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_accounts_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='billtransaction',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_billtransaction_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='billtransaction',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='billtransaction',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='billtransaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='billtransaction',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_billtransaction_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwisediscardedtransactionhead_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='entry_type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Edit'), (2, 'Merge'), (3, 'Other')], db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='organizationwisediscardedtransactionhead',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_organizationwisediscardedtransactionhead_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_patientbill_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='payment_status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Due'), (2, 'Paid'), (3, 'Partial')], db_index=True, default=1, verbose_name='payment status'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='person_organization_patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='patient_bill_person_organization', to='core.PersonOrganization', verbose_name='patient in person organization'),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='patientbill',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_patientbill_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_payabletoperson_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='group_id',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True, verbose_name='unique code for group payable'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='person_organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payable_person_organization', to='core.PersonOrganization', verbose_name='person organization'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='transaction_head',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payable_transaction_head', to='account.TransactionHead', verbose_name='transaction head'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Addition'), (2, 'Deduction'), (3, 'Other')], db_index=True, default=1, verbose_name='payable type'),
        ),
        migrations.AlterField(
            model_name='payabletoperson',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_payabletoperson_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='salestransaction',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_salestransaction_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='salestransaction',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='salestransaction',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='salestransaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='salestransaction',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_salestransaction_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='account_cheque',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='accoun_cheque_of', to='account.AccountCheque', verbose_name='account cheque'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='accounts',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='account.Accounts', verbose_name='a/c'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='admission',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='admission_transaction', to='clinic.PatientAdmission', verbose_name='for admission of'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='appointment',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_transaction', to='clinic.AppointmentTreatmentSession', verbose_name='for appointment of'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='bank',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='bank or mobile banking provider'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='branch',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='branch if any'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='unique code for group transaction'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='department',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transaction', to='clinic.OrganizationDepartment', verbose_name='department of transaction'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transaction_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='method',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Cash'), (2, 'Cheque'), (3, 'Mobile Banking'), (4, 'Bank Draft'), (5, 'Card')], db_index=True, default=0, verbose_name='method of transaction'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='paid_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='paying_by', to=settings.AUTH_USER_MODEL, verbose_name='transaction by'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='paid_by_person_organization', to='core.PersonOrganization', verbose_name='transaction by person of organization'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='person_organization_received',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='received_by_person_organization', to='core.PersonOrganization', verbose_name='employee person organization'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='received_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='receive_by', to=settings.AUTH_USER_MODEL, verbose_name='employee'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='recipt_no',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='cheque, bank draft or reference no'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='sales',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transaction_of', to='pharmacy.Sales', verbose_name='for sales of'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='service_consumed',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumed_transaction', to='clinic.ServiceConsumed', verbose_name='for service consumption of'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='service_consumed_group',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumed_group_transaction', to='clinic.ServiceConsumedGroup', verbose_name='for group service consumption of'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_for',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Sale'), (2, 'Admission'), (3, 'Appointment'), (4, 'Service Consumed'), (5, 'Others'), (6, 'Purchase')], db_index=True, default=5),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transaction_group', to='account.TransactionGroup', verbose_name='transaction group'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transaction_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='unique code for group transaction'),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactiongroup_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='serial_no',
            field=models.PositiveIntegerField(blank=True, default=None, help_text='Serial Number', null=True),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactiongroup',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactiongroup_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='department',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transaction_head', to='clinic.OrganizationDepartment', verbose_name='department of transaction head'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactionhead_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='group',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Patient'), (2, 'Employee'), (3, 'Supplier'), (4, 'Stack Holder'), (5, 'Referrer'), (6, 'Other'), (7, 'Service Provider')], db_index=True, default=0, verbose_name='group of transaction head'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='is_global',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Private'), (1, 'Global'), (2, 'Changed into Global')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Capital'), (2, 'Recurring')], db_index=True, default=1, verbose_name='type of head'),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactionhead_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='transactionpurchase',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactionpurchase_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='transactionpurchase',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name'),
        ),
        migrations.AlterField(
            model_name='transactionpurchase',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number'),
        ),
        migrations.AlterField(
            model_name='transactionpurchase',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionpurchase',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='account_transactionpurchase_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
    ]
