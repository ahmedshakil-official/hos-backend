import os

from common.enums import Status
from common.tasks import send_message_to_slack_or_mattermost_channel_lazy
from pharmacy.enums import StockIOType, PurchaseOrderStatus
from pharmacy.models import Purchase, StockIOLog, PurchaseRequisition


def send_procure_alert_to_slack(message):
    send_message_to_slack_or_mattermost_channel_lazy.delay(
        os.environ.get("HOS_PURCHASE_MONITOR_CHANNEL_ID", ""),
        message
    )


def create_requisition_for_procure_group(
        _datetime_now,
        procure_group,
        procure_items,
        organization_id,
        user,
        store_point_id,
        department_id,
        invoices
):
    invoices = ", ".join(invoices)
    data = {
        "requisition_date": _datetime_now.date(),
        "purchase_date": _datetime_now,
        "status": Status.DRAFT,
        "person_organization_receiver": user.get_person_organization_for_employee(only_fields=['id']),
        "person_organization_supplier_id": procure_group.supplier_id,
        "receiver_id": user.id,
        "supplier_id": procure_group.supplier.person_id,
        "store_point_id": store_point_id,
        "department_id": department_id,
        "entry_by_id": user.id,
        "organization_id": organization_id,
        "vouchar_no": invoices,
        "remarks": invoices,
    }
    requisition_instance = Purchase.objects.create(**data)

    for item in procure_items:
        io_item = {
            "date": _datetime_now.date(),
            "status": Status.DRAFT,
            "stock_id": item.get('stock'),
            "quantity": float(item.get('total_quantity')),
            "batch": "N/A",
            "primary_unit_id": item.get('stock__product__primary_unit'),
            "secondary_unit_id": item.get('stock__product__secondary_unit'),
            "conversion_factor": item.get('stock__product__conversion_factor'),
            "secondary_unit_flag": False,
            "type": StockIOType.INPUT,
            "entry_by_id": user.id,
            "organization_id": organization_id,
            "purchase": requisition_instance,
            "rate": float(item.get('rate')),
        }
        StockIOLog.objects.create(**io_item)

    return requisition_instance


def create_purchase_or_order_for_procure_group(
        _datetime_now,
        procure_group,
        procure_items,
        organization_id,
        user,
        store_point_id,
        reference_id,
        status,
        invoices
):
    total_amount = procure_group.total_amount
    data = {
        "amount": float(total_amount),
        "purchase_date": _datetime_now,
        "status": status,
        "person_organization_receiver": user.get_person_organization_for_employee(only_fields=['id']),
        "person_organization_supplier_id": procure_group.supplier_id,
        "receiver_id": user.id,
        "supplier_id": procure_group.supplier.person_id,
        "purchase_order_status": PurchaseOrderStatus.COMPLETED,
        "store_point_id": store_point_id,
        "entry_by_id": user.id,
        "organization_id": organization_id,
        "vouchar_no": invoices,
    }
    if status == Status.ACTIVE:
        data["copied_from_id"] = reference_id
        data["purchase_order_status"] = PurchaseOrderStatus.DEFAULT

    purchase_instance = Purchase.objects.create(**data)
    if status == Status.PURCHASE_ORDER:
        PurchaseRequisition.objects.create(
            purchase=purchase_instance,
            requisition_id=reference_id,
            organization_id=organization_id,
        )

    for item in procure_items:
        io_item = {
            "date": _datetime_now.date(),
            "status": status,
            "stock_id": item.get('stock'),
            "quantity": float(item.get('total_quantity')),
            "rate": float(item.get('rate')),
            "batch": "N/A",
            "primary_unit_id": item.get('stock__product__primary_unit'),
            "secondary_unit_id": item.get('stock__product__secondary_unit'),
            "conversion_factor": item.get('stock__product__conversion_factor'),
            "secondary_unit_flag": False,
            "type": StockIOType.INPUT,
            "entry_by_id": user.id,
            "organization_id": organization_id,
            "purchase": purchase_instance,
        }
        StockIOLog.objects.create(**io_item)

    return purchase_instance
