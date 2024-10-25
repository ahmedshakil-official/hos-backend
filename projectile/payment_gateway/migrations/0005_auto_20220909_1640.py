# Generated by Django 2.2.25 on 2022-09-09 10:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment_gateway', '0004_auto_20200225_1539'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentrequest',
            name='entry_by',
        ),
        migrations.RemoveField(
            model_name='paymentrequest',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='paymentrequest',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='paymentresponse',
            name='entry_by',
        ),
        migrations.RemoveField(
            model_name='paymentresponse',
            name='ipn',
        ),
        migrations.RemoveField(
            model_name='paymentresponse',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='PaymentIpn',
        ),
        migrations.DeleteModel(
            name='PaymentRequest',
        ),
        migrations.DeleteModel(
            name='PaymentResponse',
        ),
    ]