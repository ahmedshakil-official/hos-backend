"""Payloads for test cases will go here."""
from django.utils import timezone

from procurement.enums import ProcureIssueType

def procure_status_payload(procure_id: int):
    payload = {
        "current_status": 1,
        "procure": procure_id,
        "remarks": "Procure status remarks"
    }
    return payload


def get_procure_issue_log_payload(
    supplier_id: int, employee_id: int, stock_id: int, prediction_item_id: int
):
    return {
        "date": str(timezone.now().date()),
        "supplier": supplier_id,
        "employee": employee_id,
        "stock": stock_id,
        "prediction_item": prediction_item_id,
        "type": ProcureIssueType.OTHER,
        "remarks": "Sample Procure Issue."
    }

def procure_date_update_payload(alias, is_confirmed, type):
    if is_confirmed:
        return {
            "alias": alias,
            "is_confirmed": is_confirmed,
            "type": type,
        }
    else:
        return {
            "alias": alias,
            "type": type,
        }
