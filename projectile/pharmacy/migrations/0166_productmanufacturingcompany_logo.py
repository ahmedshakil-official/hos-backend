# Generated by Django 4.2.3 on 2023-08-17 11:20

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pharmacy", "0165_purchase_order_rating_purchase_order_rating_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="productmanufacturingcompany",
            name="logo",
            field=common.fields.TimestampVersatileImageField(
                blank=True, null=True, upload_to="logo/images"
            ),
        ),
    ]
