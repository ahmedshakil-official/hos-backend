# Generated by Django 2.2.25 on 2022-01-20 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0007_procureissuelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='procure',
            name='copied_from',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='procurement.Procure'),
        ),
    ]
