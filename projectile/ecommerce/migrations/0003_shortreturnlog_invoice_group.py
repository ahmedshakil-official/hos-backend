# Generated by Django 2.2.24 on 2021-10-21 05:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0002_orderinvoicegroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='shortreturnlog',
            name='invoice_group',
            field=models.ForeignKey(blank=True, help_text='Order invoice group for distributor order', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='invoice_groups', to='ecommerce.OrderInvoiceGroup'),
        ),
    ]