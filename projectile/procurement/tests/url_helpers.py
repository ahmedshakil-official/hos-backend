"""URL helpers for procurement app."""

from django.urls import reverse


def get_shop_names_url(name: str):
    return reverse(name)


def get_procure_url(name: str):
    return reverse(name)


def get_procure_status_url(name: str):
    return reverse(name)


def get_procure_issue_log_url(name: str)->str:
    return reverse(name)


def get_purchase_prediction_is_locked_update_url(name:str, alias)->str:
    return reverse(name, args=[alias])


def get_download_prediction_data_url(name: str) -> str:
    return reverse(name)


def get_invoice_number_for_procure_url(name: str) -> str:
    return reverse(name)


def get_procure_date_update_url() -> str:
    return reverse("procure-date-update")