# Generated by Django 2.2.9 on 2020-02-25 09:39

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('payment_gateway', '0003_paymentrequest_discount_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentipn',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='paymentrequest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='paymentresponse',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment'), (13, 'Distributor Order')], db_index=True, default=0),
        ),
    ]