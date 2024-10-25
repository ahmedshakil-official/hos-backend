# Generated by Django 2.2.20 on 2021-05-21 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='amount',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_charge',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='discount',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='discount_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='grand_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='round_discount',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='tax_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='tax_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='vat_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='vat_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='discount_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='discount_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='quantity',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='round_discount',
            field=models.DecimalField(decimal_places=3, default=0.0, help_text="discount amount distributed by inventory's round_discount", max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='tax_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='tax_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='vat_rate',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
        migrations.AlterField(
            model_name='stockdelivery',
            name='vat_total',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=19),
        ),
    ]
