# Generated by Django 2.2.25 on 2022-04-08 08:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0205_scriptfilestorage_date'),
        ('procurement', '0011_auto_20220331_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictionitem',
            name='assign_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prediction_item_assign_to', to='core.PersonOrganization'),
        ),
        migrations.AddField(
            model_name='predictionitem',
            name='real_avg',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AddField(
            model_name='predictionitem',
            name='sale_avg_3d',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AddField(
            model_name='predictionitem',
            name='team',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
    ]
