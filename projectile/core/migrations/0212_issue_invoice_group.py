# Generated by Django 2.2.25 on 2022-11-15 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0009_orderinvoicegroup_secondary_responsible_employee'),
        ('core', '0211_employeemanager'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='invoice_group',
            field=models.ForeignKey(blank=True, help_text='The order invoice group related to issue', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_invoice_group_issues', to='ecommerce.OrderInvoiceGroup'),
        ),
    ]
