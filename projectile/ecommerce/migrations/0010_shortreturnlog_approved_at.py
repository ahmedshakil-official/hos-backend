# Generated by Django 2.2.25 on 2023-01-02 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0009_orderinvoicegroup_secondary_responsible_employee'),
    ]

    operations = [
        migrations.AddField(
            model_name='shortreturnlog',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]