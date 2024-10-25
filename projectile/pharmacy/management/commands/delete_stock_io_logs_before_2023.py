from yaspin import yaspin

from django.core.management.base import BaseCommand

from delivery.models import Delivery, OrderDeliveryConnector, StockDelivery
from ecommerce.models import ShortReturnItem
from pharmacy.models import StockIOLog


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
        """Management script to delete stock io logs before 2023 with connected models data."""
        date_2023 = "2023-01-01"

        # Fetch StockIOLog instances created before 2023
        stock_io_logs = StockIOLog.objects.filter(created_at__date__lt=date_2023)

        # Collect IDs of StockIOLog instances created before 2023
        stock_io_log_ids = stock_io_logs.values_list("id", flat=True)

        # Fetch ShortReturnItem instances related to the StockIOLog instances before 2023
        short_return_items = ShortReturnItem.objects.filter(
            stock_io_id__in=stock_io_log_ids
        )

        # Delete ShortReturnItem instances related to the StockIOLog instances before 2023
        bulk_delete(qs=short_return_items)

        # Delete StockDelivery instances created before 2023
        stock_deliveries = StockDelivery.objects.filter(stock_io_id__in=stock_io_log_ids)
        bulk_delete(qs=stock_deliveries)

        # Delete OrderDeliveryConnector instances created before 2023
        order_delivery_connectors = OrderDeliveryConnector.objects.filter(
            created_at__date__lt=date_2023
        )
        bulk_delete(qs=order_delivery_connectors)

        # Delete Delivery instances created before 2023
        deliveries = Delivery.objects.filter(created_at__date__lt=date_2023)
        bulk_delete(qs=deliveries)

        # Delete StockIOLog instances created before 2023
        stock_io_logs = StockIOLog.objects.filter(created_at__date__lt=date_2023)
        bulk_delete(qs=stock_io_logs)
