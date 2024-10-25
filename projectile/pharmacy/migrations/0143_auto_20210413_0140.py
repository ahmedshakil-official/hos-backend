# Generated by Django 2.2.19 on 2021-04-12 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0142_invoicefilestorage_orderinvoiceconnector'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoicefilestorage',
            name='purpose',
        ),
        migrations.AddField(
            model_name='invoicefilestorage',
            name='orders',
            field=models.ManyToManyField(related_name='invoice_orders', through='pharmacy.OrderInvoiceConnector', to='pharmacy.Purchase'),
        ),
    ]
