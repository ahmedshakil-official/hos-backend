import os
from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import pytz
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from PyPDF2 import PdfMerger, PdfReader

from django.db.models import Prefetch
from django.conf import settings
from django.core.files import File
from common.enums import Status
from common.healthos_helpers import HealthOSHelper
from core.models import Organization
from core.helpers import get_order_ending_time
from ecommerce.models import OrderInvoiceGroup, InvoiceGroupPdf, InvoicePdfGroup
from ecommerce.utils import get_dynamic_discount_message

from pharmacy.enums import (
    DistributorOrderType,
    PurchaseType,
    OrderTrackingStatus,
)
from pharmacy.models import StockIOLog, Purchase
from projectile.celery import app

health_os_helper = HealthOSHelper()


def svg_embed(html):
    from base64 import b64encode
    from lxml import etree
    root = html.root_element
    svgs = root.findall('.//nvd3')
    for svg in svgs:
        child = svg.getchildren()[0]
        encoded = b64encode(etree.tostring(child)).decode()
        encoded_data = "data:image/svg+xml;charset=utf-8;base64," + encoded
        encoded_child = etree.fromstring('<img src="%s"/>' % encoded_data)
        svg.replace(child, encoded_child)
    return html

def makepdf(html):
    """Generate a PDF file from a string of HTML."""
    htmldoc = HTML(string=html, base_url="")
    return htmldoc.write_pdf()

def get_contact(distributor):
    mobile = distributor.get('primary_mobile', "")
    alternative_mobile = distributor.get('other_contact', "")
    email = distributor.get('email', "")
    if alternative_mobile and alternative_mobile != mobile:
        text = f"Mobile: {mobile}, {alternative_mobile} | Email: {email}"
    else:
        text = f"Mobile: {mobile} | Email: {email}"
    return text

def product_short_name(product, ignore_form=False):
    name = product.get('name')
    form = product.get('form').get('name') if product.get('form', None) else None
    strength = product.get('strength', '')
    if ignore_form:
        return f"{name} {strength}"
    if form and strength:
        return f"{form} {name} {strength}"
    if form and not strength:
        return f"{form} {name}"
    if strength and not form:
        return f"{name} {strength}"
    return f"{name}"

def get_invoice_stamp(date, delivery_date):
    order_ending_time = get_order_ending_time()
    timezone = pytz.timezone("Asia/Dhaka")
    format_string = "%Y-%m-%dT%H:%M:%S%z"
    datetime_object = datetime.strptime(date, format_string)
    delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
    combined_delivery_date_and_order_ending_time = timezone.localize(
        datetime.combine(delivery_date_obj, order_ending_time)
    )
    if datetime_object > combined_delivery_date_and_order_ending_time:
        return "6:00 AM"
    return ""

def create_barcode_image(invoice_id):
    string = f"* G-{invoice_id} *"
    source = os.path.join(settings.REPO_DIR, "projectile")
    dest = os.path.join(settings.REPO_DIR, "assets")
    code128 = barcode.get('code128', str(string), writer=ImageWriter())
    file = f"{dest}/{invoice_id}"
    filename = code128.save(file)
    # os.replace(f"{source}/{filename}", f"{dest}/{filename}")
    return filename

def to_barcode(string):
    import barcode
    from io import BytesIO
    from barcode.writer import SVGWriter

    # Write the barcode to a binary stream
    rv = BytesIO()
    code = barcode.get('code128', str(string), writer=SVGWriter())
    code.write(rv)

    rv.seek(0)
    # get rid of the first bit of boilerplate
    rv.readline()
    rv.readline()
    rv.readline()
    rv.readline()
    # read the svg tag into a string
    svg = rv.read()
    return svg.decode("utf-8")

def create_pdf(invoice_data):
    """Create PDF"""
    template_name = 'templates/html/invoice.html'
    invoice_id = invoice_data.get("id")
    outfile = f"{invoice_id}.pdf"
    template_vars = invoice_data
    env = Environment(loader=FileSystemLoader('.'))
    env.filters['to_barcode'] = to_barcode
    template = env.get_template(template_name)
    html_out = template.render(template_vars)
    pdf = makepdf(html_out)
    Path(outfile).write_bytes(pdf)
    return outfile

def get_queryset(invoice_ids):
    order_items = StockIOLog.objects.filter(
        status=Status.DISTRIBUTOR_ORDER,
    ).select_related(
        'stock__product__form',
        'stock__product__compartment',
    )
    order_filters = {
        "status": Status.DISTRIBUTOR_ORDER,
        "distributor_order_type": DistributorOrderType.ORDER,
        "purchase_type": PurchaseType.VENDOR_ORDER,
        "distributor_id": health_os_helper.organization_id()
    }
    orders = Purchase.objects.filter(
        **order_filters
    ).only(
        'id',
        'grand_total',
        'invoice_group_id',
    ).prefetch_related(
        Prefetch(
            "stock_io_logs",
            queryset=order_items,
        ),
    )
    queryset = OrderInvoiceGroup.objects.filter(
        pk__in=invoice_ids,
        status=Status.ACTIVE,
        organization__id=health_os_helper.organization_id(),
        orders__isnull=False
    ).select_related(
        'responsible_employee',
        'order_by_organization',
        'order_by_organization__primary_responsible_person',
        'order_by_organization__area',
    ).prefetch_related(
        Prefetch(
            'orders',
            queryset=orders
        )
    ).distinct()
    return queryset

def serialize_data(queryset):
    from ecommerce.serializers.order_invoice_group import OrderInvoiceGroupModelSerializer
    return OrderInvoiceGroupModelSerializer.DetailsForPDF(
        queryset,
        many=True
    ).data

def prepare_person_data(person_data):
    if not isinstance(person_data, OrderedDict):
        return ""
    first_name = person_data.get("first_name", "")
    last_name = person_data.get("last_name", "")
    code = person_data.get("code", "")
    full_name = f"{first_name} {last_name}"
    if code:
        full_name = f"{full_name} - {code}"
    return full_name

def prepare_area(order_by_organization):
    area = order_by_organization.get("area", {})
    if not isinstance(area, OrderedDict):
        return ""
    name = area.get("name", "")
    return name

def prepare_products(invoice_data):
    orders = invoice_data.get("orders", [])
    items = []
    compartments = []
    order_ids = []
    total_order_qty = 0
    total_short_qty = 0
    for order in orders:
        stock_io_logs = order.get("stock_io_logs", [])
        for io_item in stock_io_logs:
            stock_id = io_item["stock"]["id"]
            order_ids.append(order.get("id", ""))
            try:
                compartment_object = dict(io_item["stock"]["product"]["compartment"])
            except Exception as _:
                compartment_object = {
                    "id": 0,
                    "name": "Others",
                    "priority": 0
                }

            product_object = {
                "product_name": product_short_name(io_item["stock"]["product"]),
                "product_name_for_sorting": product_short_name(io_item["stock"]["product"], True),
                "stock_id": stock_id,
                "rate": io_item.get("rate", 0),
                "quantity": io_item.get("quantity", 0),
                "short_quantity": 0,
                "discount_total": io_item.get("discount_total", 0),
                "discount_rate": io_item.get("discount_rate", 0),
                "compartment_id": compartment_object.get("id", 0),
                "compartment_name": compartment_object.get("name", "Others"),
                "compartment_priority": compartment_object.get("priority", 0)
            }
            items.append(product_object)
            compartments.append(compartment_object)
            total_order_qty += product_object["quantity"]

    df = pd.DataFrame(items)
    compartment_df = pd.DataFrame(compartments)
    compartment_df = compartment_df.drop_duplicates(subset=["id"]).sort_values("priority", ascending=False)
    compartment_df = compartment_df.rename(columns={"name": "compartment_name"})

    # Group by stock_id, rate and discount_rate and sum the quantity column
    grouped_df = df.groupby(["stock_id", "rate", "discount_rate"]).agg({'quantity': 'sum', 'discount_total': 'sum'}).reset_index()
    # Merge the aggregated results back to the original DataFrame
    result_df = pd.merge(df, grouped_df, on=["stock_id", "rate", "discount_rate"], how="left", suffixes=('', '_sum'))
    # Drop duplicate data
    result_df = result_df.drop_duplicates(subset=["stock_id", "rate", "discount_rate"])
    # Update quantity
    result_df["quantity"] = result_df["quantity_sum"]
    result_df["discount_total"] = result_df["discount_total_sum"]
    result_df["amount"] = result_df["quantity"] *  result_df["rate"]
    result_df["net_pay"] = result_df["amount"] - result_df["discount_total"]
    result_df = result_df.drop("quantity_sum", axis=1)
    # Group by 'compartment_name' and sort each group by 'compartment_priority'
    sorted_df = result_df.sort_values("compartment_priority", ascending=False).groupby("compartment_name").apply(
        lambda x: x[[
            "product_name",
            "product_name_for_sorting",
            "rate", "quantity",
            "short_quantity",
            "amount",
            "discount_total",
            "net_pay"]].sort_values("product_name_for_sorting", ascending=True).to_dict(orient='records')
    ).reset_index(name="stock_io_logs")
    # Merge with sorted compartment data
    final_df = pd.merge(compartment_df, sorted_df, on="compartment_name", how="left")
    final_df = final_df.rename(columns={"compartment_name": "name"})
    product_data = final_df.to_dict(orient='records')
    last_index = 0
    for item in product_data:
        for io_item in item["stock_io_logs"]:
            last_index += 1
            io_item["sl_no"] = last_index
    return product_data, order_ids, total_order_qty, total_short_qty



def prepare_order_by_organization(invoice_data):
    order_by_organization = invoice_data.get("order_by_organization", {})
    if not isinstance(order_by_organization, OrderedDict):
        return {}
    primary_responsible_person = order_by_organization.get("primary_responsible_person", {})
    order_by_organization["primary_responsible_person"] = prepare_person_data(primary_responsible_person)
    order_by_organization["area"] = prepare_area(order_by_organization)
    return dict(order_by_organization)

def get_invoice_id_str(invoice_id, order_ids):
    order_id_str = ", ".join([f"#{item}" for item in order_ids])
    return f"{invoice_id} ({order_id_str})"

def prepare_invoice_data(invoice_data):
    invoice_data["order_by_organization"] = prepare_order_by_organization(invoice_data)
    invoice_data["compartments"], invoice_data["order_ids"], invoice_data["total_quantity"], invoice_data["total_short_quantity"] = prepare_products(invoice_data)
    invoice_data.pop("orders", [])
    invoice_data["sub_total"] = Decimal(invoice_data.get("sub_total", 0))
    invoice_data["discount"] = Decimal(invoice_data.get("discount", 0))
    invoice_data["round_discount"] = Decimal(invoice_data.get("round_discount", 0))
    invoice_data["additional_discount"] = Decimal(invoice_data.get("additional_discount", 0))
    invoice_data["additional_cost"] = Decimal(invoice_data.get("additional_cost", 0))
    invoice_data["total_short"] = Decimal(invoice_data.get("total_short", 0))
    invoice_data["total_return"] = Decimal(invoice_data.get("total_return", 0))
    invoice_data["invoice_id_str"] = get_invoice_id_str(invoice_data.get("id"), invoice_data.get("order_ids"))
    grand_total = (
        invoice_data.get("sub_total", 0) -
        invoice_data.get("discount", 0) +
        invoice_data.get("round_discount", 0) -
        invoice_data.get("additional_discount", 0) +
        invoice_data.get("additional_cost", 0) -
        invoice_data.get("total_short", 0) -
        invoice_data.get("total_return", 0)
    )
    max_returnable_percentage = 20
    max_returnable_amount = round((max_returnable_percentage * grand_total) / 100, 3)
    invoice_data["grand_total"] = grand_total
    invoice_data["max_returnable_amount"] = max_returnable_amount
    invoice_data["dynamic_discount_message"] = get_dynamic_discount_message(
        discount_percentage=invoice_data.get("additional_dynamic_discount_percentage", 0)
    )
    return invoice_data

def store_invoice_pdf_group(file, invoice_ids, repeat, delivery_date, area):

    with open(file, 'rb') as fi:
        outfile = File(fi, name=os.path.basename(fi.name))
        pdf_reader = PdfReader(fi)
        page_count = len(pdf_reader.pages)
        InvoicePdfGroup.objects.get_or_create(
            defaults={"content": outfile},
            status=Status.ACTIVE,
            repeat=repeat,
            page_count=page_count,
            invoice_count=len(invoice_ids),
            delivery_date=delivery_date,
            invoice_groups=invoice_ids,
            area_id=area
        )
        if Path(file).is_file():
            os.remove(file)

def merge_pdf(invoice_ids, outfile_name, repeat, delivery_date, area):
    # source = os.path.join(settings.REPO_DIR, "projectile")
    # dest = os.path.join(settings.REPO_DIR, "assets")
    merger = PdfMerger()
    output_file = outfile_name

    for invoice_id in invoice_ids:
        pdf = f"{invoice_id}.pdf"
        if Path(pdf).is_file():
            for _ in range(repeat):
                merger.append(pdf)

    merger.write(output_file)
    merger.close()

    store_invoice_pdf_group(
        output_file,
        invoice_ids,
        repeat,
        delivery_date,
        area
    )

def store_file(file, invoice_id, entry_by_id=None):
    with open(file, 'rb') as fi:
        outfile = File(fi, name=os.path.basename(fi.name))
        obj, created = InvoiceGroupPdf.objects.get_or_create(
            defaults={"content": outfile, "invoice_group_id": invoice_id, "entry_by_id": entry_by_id},
            # content=outfile,
            status=Status.ACTIVE,
            invoice_group_id=invoice_id,
            entry_by_id=entry_by_id
        )

def prepare_invoice_group_context(invoice_ids, delivery_date, area):
    org_fields_to_be_fetched = [
        "name",
        "email",
        "primary_mobile",
        "other_contact",
        "address",
    ]
    organization_info = Organization.objects.only(
        *org_fields_to_be_fetched
    ).get(id=health_os_helper.organization_id())
    organization_info = organization_info.to_dict(
        _fields=org_fields_to_be_fetched
    )
    organization_info["contact"] = f"{organization_info['primary_mobile']}, {organization_info['other_contact']}"
    invoice_qs = get_queryset(invoice_ids=invoice_ids).order_by(
        "order_by_organization__primary_responsible_person",
        "order_by_organization__delivery_thana",
        "order_by_organization__delivery_sub_area",
        "-pk"
    )
    serialized_data = serialize_data(queryset=invoice_qs)
    # destination where the temp files will be created
    dest = os.path.join(settings.REPO_DIR, "assets")
    valid_invoice_id_list = []
    for data in serialized_data:
        invoice_id = data.get("id")
        valid_invoice_id_list.append(invoice_id)
        context = {
            "organization": organization_info,
            "header_title": "Invoice",
            "timestamp": get_invoice_stamp(
                data.get("date"),
                data.get("delivery_date")
            ),
            "barcode": create_barcode_image(invoice_id),
            **prepare_invoice_data(data)
        }
        file = create_pdf(invoice_data=context)
        store_file(
            file,
            invoice_id,
            entry_by_id=None
        )
    # Create a new pdf with merging all pdfs and store it
    repeat = 2
    out_file_name = f"{delivery_date}:{valid_invoice_id_list[0]}-{valid_invoice_id_list[-1]}.pdf"
    merge_pdf(valid_invoice_id_list, out_file_name, repeat, delivery_date, area)
    # Remove Pdfs and barcodes
    for invoice_id in valid_invoice_id_list:
        pdf = f"{invoice_id}.pdf"
        if Path(pdf).is_file():
            os.remove(pdf)

        if Path(f"{dest}/{invoice_id}.png").is_file():
            os.remove(f"{dest}/{invoice_id}.png")

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def create_invoice_pdf_lazy(invoice_ids, delivery_date, area):
    prepare_invoice_group_context(invoice_ids, delivery_date, area)

def create_invoice_pdf_chunk_lazy(invoice_ids, delivery_date):
    number_of_key = len(invoice_ids)
    index = 0
    chunk_size = 50

    while index < number_of_key:
        new_index = index + chunk_size
        create_invoice_pdf_lazy.apply_async(
            (invoice_ids[index:new_index], delivery_date),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        index = new_index

def get_area_key_for_invoice(invoice_id):
    invoice = OrderInvoiceGroup.objects.get(id=invoice_id)
    area = invoice.order_by_organization.area.id
    return area

def create_invoice_pdf_on_invoice_group_create_lazy(invoice_ids, delivery_date):
    # This method will first the re order invoice not create pdf yet and merge the ids with new group for creating invoice pdf
    invoice_pdf_group = InvoicePdfGroup.objects.filter(
        status=Status.ACTIVE,
        delivery_date=delivery_date,
    )
    invoice_pdf_group = invoice_pdf_group.values_list("invoice_groups", flat=True)
    invoice_id_list_already_have_pdf_group = list(chain(*invoice_pdf_group))
    invoice_id_list = invoice_ids
    previously_generated_invoice_groups = OrderInvoiceGroup.objects.filter(
        status=Status.ACTIVE,
        pk__lt=invoice_id_list[0],
        delivery_date=delivery_date,
    ).exclude(
        pk__in=invoice_id_list + invoice_id_list_already_have_pdf_group,
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.CANCELLED,
            OrderTrackingStatus.REJECTED,
        ]
    ).values_list("pk", flat=True)

    final_invoice_id_list = list(previously_generated_invoice_groups) + invoice_id_list
    # get sorted invoice group with final invoice group id list
    # we need to sort by responsible employee area then sub area as operation team works on this order
    sorted_invoice_ids = OrderInvoiceGroup.objects.filter(
        id__in = final_invoice_id_list
    ).order_by(
        "order_by_organization__primary_responsible_person",
        "order_by_organization__delivery_thana",
        "order_by_organization__delivery_sub_area",
        "-pk",
    ).values_list("pk", flat=True)

    final_invoice_id_list = list(sorted_invoice_ids)

    # Grouping invoice IDs by area
    invoices_by_area = defaultdict(list)
    for invoice_id in final_invoice_id_list:
        area_key = get_area_key_for_invoice(invoice_id)
        invoices_by_area[area_key].append(invoice_id)

    # Processing each area separately
    for area, invoice_ids in invoices_by_area.items():
        # Passing invoice IDs for the current area to the task
        create_invoice_pdf_lazy.apply_async(
            (invoice_ids, delivery_date, area),
            countdown=5,
            retry=True,retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
