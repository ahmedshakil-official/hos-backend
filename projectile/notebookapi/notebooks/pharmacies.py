from datetime import datetime, timedelta, time

from pytz import timezone

from django.db.models import Max, Count

import pandas as pd

from pharmacy.models import OrderTracking


def get_dropped_pharmacies(days_ago=None, drop_days=None):
    if days_ago is None:
        days_ago = 120

    if drop_days is None:
        drop_days = 7

    date_from = (
        datetime.now(
            timezone('Asia/Dhaka')
        ) - timedelta(days_ago)
    ).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )

    drop_date = (
        datetime.now(
            timezone('Asia/Dhaka')
        ) - timedelta(drop_days)
    ).replace(
        hour=0, minute=0, second=0, microsecond=0,
    ).date()

    date_till = (
        datetime.now(
            timezone('Asia/Dhaka')
        )
    ).replace(
        hour=23, minute=59, second=59, microsecond=999999,
    )

    active_pharmacy_id = list(set(OrderTracking.objects.filter(
        date__range=[drop_date, date_till],
    ).values_list(
        'order__organization_id', flat=True
    )))

    area = {
        'ADABOR': 302602,
        'BADDA': 302604,
        'BANGSHAL': 302605,
        'BIMAN_BANDAR': 302606,
        'BANANI': 302607,
        'CANTONMENT': 302608,
        'CHAK_BAZAR': 302609,
        'DAKSHINKHAN': 302610,
        'DARUS_SALAM': 302611,
        'DEMRA': 302612,
        'DHAMRAI': 302614,
        'DHANMONDI': 302616,
        'DOHAR': 302618,
        'BHASAN_TEK': 302621,
        'BHATARA': 302622,
        'GENDARIA': 302624,
        'GULSHAN': 302626,
        'HAZARIBAGH': 302628,
        'JATRABARI': 302629,
        'KAFRUL': 302630,
        'KADAMTALI': 302632,
        'KALABAGAN': 302633,
        'KAMRANGIR_CHAR': 302634,
        'KHILGAON': 302636,
        'KHILKHET': 302637,
        'KERANIGANJ': 302638,
        'KOTWALI': 302640,
        'LALBAGH': 302642,
        'MIRPUR': 302648,
        'MOHAMMADPUR': 302650,
        'MOTIJHEEL': 302654,
        'MUGDA_PARA': 302657,
        'NAWABGANJ': 302662,
        'NEW_MARKET': 302663,
        'PALLABI': 302664,
        'PALTAN': 302665,
        'RAMNA': 302666,
        'RAMPURA': 302667,
        'SABUJBAGH': 302668,
        'RUPNAGAR': 302670,
        'SAVAR': 302672,
        'SHAHJAHANPUR': 302673,
        'SHAH_ALI': 302674,
        'SHAHBAGH': 302675,
        'SHYAMPUR': 302676,
        'SHER_E_BANGLA_NAGAR': 302680,
        'SUTRAPUR': 302688,
        'TEJGAON': 302690,
        'TEJGAON_IND_AREA': 302692,
        'TURAG': 302693,
        'UTTARA_PASCHIM': 302694,
        'UTTARA_PURBA': 302695,
        'UTTAR_KHAN': 302696,
        'WARI': 302698,
        'OTHER1': 888888,
        'OTHER2': 999999,
    }

    order_trackings = OrderTracking.objects.filter(
        date__range=[date_from, date_till],
    ).exclude(
        order__organization_id__in=active_pharmacy_id
    ).select_related(
        'order',
    ).values(
        'order__organization_id',
        'order__organization__name',
        'order__organization__primary_mobile',
        'order__organization__address',
        'order__organization__delivery_thana',
        'order__organization__primary_responsible_person__first_name',
        'order__organization__primary_responsible_person__last_name',
    ).annotate(
        last_order=Max('order__tentative_delivery_date'),
        count_order=Count('order__tentative_delivery_date', distinct=True)
    )

    data = pd.DataFrame(order_trackings)

    for item in area:
        data.loc[data['order__organization__delivery_thana'] ==
                 area[item], 'order__organization__delivery_thana'] = item

    data.rename(
        columns={
            'order__organization_id': 'organization_id',
            'order__organization__name': 'pharmacy_name',
            'order__organization__primary_mobile': 'phone',
            'order__organization__address': 'address',
            'order__organization__delivery_thana': 'area',
            'order__organization__primary_responsible_person__first_name': 'first_name',
            'order__organization__primary_responsible_person__last_name': 'last_name'
        },
        inplace=True
    )

    data['responsible_person'] = data['first_name'] + " " + data['last_name']

    data.drop(['first_name', 'last_name'], axis=1)

    json_data = data.to_json(orient='records')
    return json_data
