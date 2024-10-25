from yaspin import yaspin

from django.core.management.base import BaseCommand

from core.models import Issue, IssueStatus
from ecommerce.models import ShortReturnLog
from pharmacy.models import (
    StockIOLog,
    Purchase,
    PurchaseRequisition,
    OrderTracking,
    OrderInvoiceConnector
)
from procurement.models import Procure, ProcureItem


def bulk_delete(qs, chunk_size=50000):
    # Function to delete instances in bulk with a spinner feedback
    model_name = qs.model.__name__
    chunk_size = chunk_size
    total_data = qs.count()
    number_of_iteration = int((total_data / chunk_size) + 1)
    lower_limit = 0
    upper_limit = chunk_size
    count = 0
    spinner_text = f"Deleting {total_data} rows of {model_name} Model"
    with yaspin(text=spinner_text, color="yellow") as spinner:
        if total_data < 1:
            spinner.fail(f"💥 No data found for deleting of {model_name}")
            return
        for _ in range(0, number_of_iteration):
            qs = qs.all()
            instances_to_be_deleted = qs[lower_limit:upper_limit]
            count += instances_to_be_deleted.count()
            instances_to_be_deleted._raw_delete(instances_to_be_deleted.db)
            spinnner_d_text = f"> Done {count} of {total_data} {model_name} Model"
            spinner.write(spinnner_d_text)
        spinner.ok("✅")


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Management script to delete purchase and related models data created before 2023."""
        date_2023 = "2023-01-01"

        # Fetch Purchase instances created before 2023
        purchases = Purchase.objects.filter(created_at__date__lt=date_2023)
        purchase_ids = purchases.values_list("id", flat=True)

        # Delete related PurchaseRequisition instances
        purchase_requisitions = PurchaseRequisition.objects.filter(purchase_id__in=purchase_ids)
        bulk_delete(qs=purchase_requisitions)

        # Delete related OrderTracking instances
        order_trackings = OrderTracking.objects.filter(order_id__in=purchase_ids)
        bulk_delete(qs=order_trackings)

        # Delete related ShortReturnLog instances
        short_return_logs = ShortReturnLog.objects.filter(order_id__in=purchase_ids)
        bulk_delete(qs=short_return_logs)

        # Delete related IssueStatus instances
        issues = Issue.objects.filter(order_id__in=purchase_ids)
        issue_ids = issues.values_list("id", flat=True)
        issue_status = IssueStatus.objects.filter(issue_id__in=issue_ids)
        bulk_delete(qs=issue_status)

        # Delete related Issue instances
        bulk_delete(qs=issues)

        # Delete related OrderInvoiceConnector instances
        order_invoice_connectors = OrderInvoiceConnector.objects.filter(order_id__in=purchase_ids)
        bulk_delete(qs=order_invoice_connectors)

        # Fetch Procure instances related to Purchase
        procures = Procure.objects.filter(requisition_id__in=purchase_ids)
        procure_ids = procures.values_list("id", flat=True)

        # Delete related ProcureItem instances
        procure_items = ProcureItem.objects.filter(procure_id__in=procure_ids)
        bulk_delete(qs=procure_items)

        # Delete Procure instances
        bulk_delete(qs=procures)

        # Delete StockIOLog instances related to Purchase
        stock_io_logs = StockIOLog.objects.filter(purchase_id__in=purchase_ids)
        bulk_delete(qs=stock_io_logs)

        # Delete the main Purchase instances
        bulk_delete(qs=purchases)
