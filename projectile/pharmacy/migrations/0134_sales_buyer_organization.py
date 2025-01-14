# Generated by Django 2.2.13 on 2020-08-10 06:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0186_organization_delivery_thana'),
        ('pharmacy', '0133_stock_avg_purchase_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='buyer_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='buyer_sales', to='core.Organization'),
        ),
    ]
