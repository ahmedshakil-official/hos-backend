from yaspin import yaspin  # Importing the yaspin library for creating a spinner

# Importing necessary Django modules and models
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Issue, IssueStatus
from ecommerce.models import (
    OrderInvoiceGroup,
    ShortReturnLog,
    InvoiceGroupDeliverySheet,
    DeliverySheetInvoiceGroup,
    DeliverySheetItem,
    TopSheetSubTopSheet,
)


# Function to delete instances in bulk with a spinner feedback
def bulk_delete(qs, chunk_size=50000):
    model_name = qs.model.__name__  # Fetching the name of the model
    chunk_size = chunk_size  # Setting the chunk size for bulk deletion
    total_data = qs.count()  # Counting the total number of instances to be deleted
    number_of_iteration = int(
        (total_data / chunk_size) + 1
    )  # Calculating the number of iterations required
    lower_limit = 0
    upper_limit = chunk_size
    count = 0
    spinner_text = (
        f"Deleting {total_data} rows of {model_name} Model"  # Text for the spinner
    )
    with yaspin(
        text=spinner_text, color="yellow"
    ) as spinner:  # Creating a spinner with the specified text and color
        if total_data < 1:
            spinner.fail(
                f"💥 No data found for deleting of {model_name}"
            )  # Spinner failure message if no data is found
            return
        for _ in range(0, number_of_iteration):  # Iterating through chunks for deletion
            qs = qs.all()
            instances_to_be_deleted = qs[lower_limit:upper_limit]
            count += instances_to_be_deleted.count()
            instances_to_be_deleted._raw_delete(
                instances_to_be_deleted.db
            )  # Deleting instances in bulk
            spinnner_d_text = f"> Done {count} of {total_data} {model_name} Model"  # Text showing progress
            spinner.write(spinnner_d_text)  # Updating spinner with progress info
        spinner.ok("✅")  # Marking the spinner as success after deletion completion


# Custom Django management command
class Command(BaseCommand):
    def handle(self, *args, **options):
        """Management script to delete stock io logs before 2023 with connected models data."""

        date_2023 = "2023-01-01"  # Date threshold for deletion

        # Filtering instances based on date
        order_invoice_groups = OrderInvoiceGroup.objects.filter(
            created_at__date__lt=date_2023
        )
        order_invoice_group_ids = order_invoice_groups.values_list("id", flat=True)
        short_return_logs = ShortReturnLog.objects.filter(
            invoice_group_id__in=order_invoice_group_ids
        )
        issues = Issue.objects.filter(invoice_group_id__in=order_invoice_group_ids)
        issue_ids = issues.values_list("id", flat=True)
        issue_status = IssueStatus.objects.filter(issue_id__in=issue_ids)
        invoice_group_delivery_sheets = InvoiceGroupDeliverySheet.objects.filter(
            created_at__date__lt=date_2023
        )
        invoice_group_delivery_sheet_ids = invoice_group_delivery_sheets.values_list(
            "id", flat=True
        )
        delivery_sheet_items = DeliverySheetItem.objects.filter(
            invoice_group_delivery_sheet_id__in=invoice_group_delivery_sheet_ids
        )
        delivery_sheet_item_ids = delivery_sheet_items.values_list("id", flat=True)
        delivery_sheet_invoice_groups = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item_id__in=delivery_sheet_item_ids
        )
        top_sheet_sub_top_sheets = TopSheetSubTopSheet.objects.filter(
            Q(top_sheet_id__in=invoice_group_delivery_sheet_ids)
            | Q(sub_top_sheet_id__in=invoice_group_delivery_sheet_ids)
        )

        # Bulk deletion of instances for each model
        bulk_delete(qs=issue_status)
        bulk_delete(qs=issues)
        bulk_delete(qs=short_return_logs)
        bulk_delete(qs=delivery_sheet_invoice_groups)
        bulk_delete(qs=delivery_sheet_items)
        bulk_delete(qs=order_invoice_groups)
        bulk_delete(qs=top_sheet_sub_top_sheets)
        bulk_delete(qs=invoice_group_delivery_sheets)
