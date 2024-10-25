import os
import datetime
import asyncio
import shutil
import time
from validator_collection import checkers
from django.http import HttpResponse
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from common.tasks import delete_directory_lazy
from common.file_helpers import download_multiple_pdfs, create_zip, merge_pdfs
from ecommerce.invoice_pdf_helpers import create_invoice_pdf_chunk_lazy

from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsNurse,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    IsSuperUser,
    StaffIsMonitor,
    StaffIsSalesReturn,
    StaffIsAdjustment,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
)
from core.helpers import (
    get_order_ending_time,
)

from pharmacy.utils import (
    get_tentative_delivery_date,
)

from ecommerce.filters import OrderInvoiceGroupListFilter, InvoiceGroupPdfListFilter
from ecommerce.models import InvoiceGroupPdf,OrderInvoiceGroup

class FetchingDeliveryDate(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        current_date = datetime.datetime.now()
        tentative_delivery_date = get_tentative_delivery_date(current_date, False)
        order_ending_time = get_order_ending_time()
        return Response({
                "order_ending_time": order_ending_time,
                "tentative_delivery_date": tentative_delivery_date
            },
            status=status.HTTP_200_OK
        )

class DownloadInvoiceFiles(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
        StaffIsSalesCoordinator,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        # File type zip / pdf
        file_type = self.request.GET.get("file_type", "pdf")
        id_range_min = self.request.GET.get("id_range_min", "")
        id_range_max = self.request.GET.get("id_range_max", "")
        file_name = f"{id_range_min}-{id_range_max}"
        repeat = self.request.GET.get("repeat", 2)
        if checkers.is_numeric(repeat):
            repeat = int(repeat)
        invoice_groups = OrderInvoiceGroup().get_all_actives().filter(
            organization__id=self.request.user.organization_id,
            orders__isnull=False
        ).distinct()
        # Return error if no invoice group found
        if not invoice_groups.exists():
            return Response(
                {"detail": "No Invoice Group found with this filters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice_groups = OrderInvoiceGroupListFilter(request.GET, queryset=invoice_groups).qs
        invoice_pdfs = InvoiceGroupPdf().get_all_actives()
        invoice_group_pks = invoice_groups.values_list("pk", flat=True)
        total_invoice_count = invoice_group_pks.count()
        invoice_pdfs = invoice_pdfs.filter(
            invoice_group__id__in=invoice_group_pks
        )
        invoice_pdf_pks = invoice_pdfs.values_list("invoice_group", flat=True)
        total_invoice_pdf_count = invoice_pdf_pks.count()
        file_urls = list(invoice_pdfs.values_list("content", flat=True))
        if total_invoice_count != total_invoice_pdf_count:
            missing_count = total_invoice_count - total_invoice_pdf_count
            missing_invoices = list(set(invoice_group_pks) ^ set(invoice_pdf_pks))
            # Run a celery task for creating the missing invoices
            create_invoice_pdf_chunk_lazy(invoice_ids=missing_invoices)
            return Response(
                {"detail": f"{missing_count} Invoice missing in PDF, please try again after some time"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # prepare absolute url for localhost
        if request.META.get("REMOTE_ADDR") in ["127.0.0.1", "::1"]:
            host = request.META.get("HTTP_HOST", "")
            host = f"http://{host}"
            file_urls = list(map(lambda element: f"{host}/{settings.FULL_MEDIA_URL}{element}", file_urls))
        else:
            file_urls = list(map(lambda element: f"{settings.FULL_MEDIA_URL}{element}", file_urls))
        if file_type.lower() == "zip":
            destination_folder = f"assets/invoice-files/zip/{file_name}"
            os.makedirs(destination_folder, exist_ok=True)

            # Run the event loop to download files
            asyncio.run(download_multiple_pdfs(file_urls, destination_folder))

            zip_file_name = f"{destination_folder}/{file_name}.zip"
            # Create a zip file from downloaded PDFs
            asyncio.run(create_zip(destination_folder, zip_file_name))

            with open(zip_file_name, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_file_name}"'
            # Delete the directory after 10 min
            delete_directory_lazy.apply_async(
                (f"{settings.REPO_DIR}/{destination_folder}",),
                countdown=600,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )

            return response

        if file_type.lower() == "pdf":
            destination_folder = f"assets/invoice-files/pdf/{file_name}"
            os.makedirs(destination_folder, exist_ok=True)


            duplicates = repeat  # Adjust the number of duplicates as needed

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            merger = loop.run_until_complete(merge_pdfs(file_urls, duplicates=duplicates))

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'

            merger.write(response)
            # Delete the directory after 10 min
            delete_directory_lazy.apply_async(
                (f"{settings.REPO_DIR}/{destination_folder}",),
                countdown=600,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )

            return response
        return Response(
            {"detail": "Seems file_type is missing"},
            status=status.HTTP_400_BAD_REQUEST
        )
