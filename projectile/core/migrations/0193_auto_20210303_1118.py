# Generated by Django 2.2.13 on 2021-03-03 05:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0192_auto_20210222_1736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='order',
            field=models.ForeignKey(blank=True, help_text='The order for related to issue', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_issues', to='pharmacy.Purchase'),
        ),
    ]
