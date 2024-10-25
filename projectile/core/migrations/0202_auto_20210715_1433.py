# Generated by Django 2.2.20 on 2021-07-15 08:33

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0201_auto_20210714_1410'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='delivery_thana',
            field=enumerify.fields.SelectIntegerField(blank=True, choices=[(0, '-'), (302602, 'Adabor'), (302604, 'Badda'), (302605, 'Bangshal'), (302606, 'Biman Bandar'), (302607, 'Banani'), (302608, 'Cantonment'), (302609, 'Chak Bazar'), (302610, 'Dakshinkhan'), (302611, 'Darus Salam'), (302612, 'Demra'), (302614, 'Dhamrai'), (302616, 'Dhanmondi'), (302618, 'Dohar'), (302621, 'Bhasantek'), (302622, 'Bhatara'), (302624, 'Gendaria'), (302626, 'Gulshan'), (302628, 'Hazaribagh'), (302629, 'Jatrabari'), (302630, 'Kafrul'), (302632, 'Kadamtali'), (302633, 'Kalabagan'), (302634, 'Kamrangir Char'), (302636, 'Khilgaon'), (302637, 'Khilkhet'), (302638, 'Keraniganj'), (302640, 'Kotwali'), (302642, 'Lalbagh'), (302648, 'Mirpur'), (302650, 'Mohammadpur'), (302654, 'Motijheel'), (302657, 'Mugda Para'), (302662, 'Nawabganj'), (302663, 'Newmarket'), (302664, 'Pallabi'), (302665, 'Paltan'), (302666, 'Ramna'), (302667, 'Rampura'), (302668, 'Sabujbagh'), (302670, 'Rupnagar'), (302672, 'Savar'), (302673, 'Shahjahanpur'), (302674, 'Shah_ali'), (302675, 'Shahbagh'), (302676, 'Shyampur'), (302680, 'Sher-e-bangla Nagar'), (302688, 'Sutrapur'), (302690, 'Tejgaon'), (302692, 'Tejgaon Industrial Area'), (302693, 'Turag'), (302694, 'Uttara Paschim'), (302695, 'Uttara Purba'), (302696, 'Uttar Khan'), (302698, 'Wari'), (888888, 'Hatirjheel'), (999999, 'Others')], db_index=True, default=None, null=True),
        ),
    ]