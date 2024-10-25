from django.db.models.query import QuerySet
from django.db.models import (
    Min,
    Max,
)
from .tasks import send_push_notification_to_mobile_app_by_org

def send_push_notification_to_mobile_app_by_org_ids(org_ids, title, body, data=""):

    if isinstance(org_ids, QuerySet):
        organizations = []
        data_length = org_ids.count()
        chunk_size = 100
        number_of_operations = int((data_length / chunk_size) + 1)
        lower_limit = 0
        upper_limit = chunk_size
        for _ in range(0, number_of_operations):
            data_limit = org_ids[lower_limit : upper_limit]
            dict_ = data_limit.aggregate(Max('id'), Min('id'))
            min_id = dict_.get('id__min', None)
            max_id = dict_.get('id__max', None)
            lower_limit = upper_limit
            upper_limit += chunk_size
            if min_id and max_id:
                send_push_notification_to_mobile_app_by_org.delay(
                    org_ids=organizations,
                    title=title,
                    body=body,
                    data={},
                    min_id=min_id,
                    max_id=max_id
                )

    elif isinstance(org_ids, list):
        data_length = len(org_ids)
        chunk_size = 100
        number_of_operations = int((data_length / chunk_size) + 1)
        lower_limit = 0
        upper_limit = chunk_size
        for _ in range(0, number_of_operations):
            data_limit = org_ids[lower_limit : upper_limit]
            lower_limit = upper_limit
            upper_limit += chunk_size
            if data_limit:
                send_push_notification_to_mobile_app_by_org.delay(
                    org_ids=data_limit,
                    title=title,
                    body=body,
                    data={},
                )