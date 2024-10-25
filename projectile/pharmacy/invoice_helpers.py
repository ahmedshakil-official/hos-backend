from pathlib import Path
import sys
import os
import os
from datetime import datetime
from projectile.celery import app
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from PyPDF2 import PdfFileMerger, PdfFileReader

from django.db.models import Prefetch
from django.core.files import File
from django.conf import settings
from common.enums import Status
from core.models import Organization
from core.enums import DhakaThana
from pharmacy.enums import DistributorOrderType, PurchaseType
from pharmacy.custom_serializer.purchase import (
    DistributorOrderDetailsGetForDistributorSerializer,
)
from pharmacy.models import StockIOLog, Purchase, InvoiceFileStorage, OrderInvoiceConnector


def get_order(order_id):
    order_items = StockIOLog.objects.filter(
        status=Status.DISTRIBUTOR_ORDER,
    ).select_related(
        'primary_unit',
        'secondary_unit',
        # 'stock__product',
        'stock__store_point',
        'stock__product__manufacturing_company',
        'stock__product__form',
        'stock__product__subgroup__product_group',
        'stock__product__generic',
        'stock__product__primary_unit',
        'stock__product__secondary_unit',
        'stock__product__category',
    ).only(
        'id',
        'alias',
        'status',
        'stock',
        'quantity',
        'rate',
        'batch',
        'expire_date',
        'date',
        'type',
        'primary_unit__id',
        'primary_unit__alias',
        'primary_unit__name',
        'primary_unit__description',
        'primary_unit__created_at',
        'primary_unit__updated_at',
        'secondary_unit__id',
        'secondary_unit__alias',
        'secondary_unit__name',
        'secondary_unit__description',
        'secondary_unit__created_at',
        'secondary_unit__updated_at',
        'discount_rate',
        'discount_total',
        'vat_rate',
        'vat_total',
        'tax_total',
        'tax_rate',
        'conversion_factor',
        'secondary_unit_flag',
        'data_entry_status',
        'purchase_id',
            'stock__id',
            'stock__alias',
            'stock__stock',
            'stock__demand',
            'stock__auto_adjustment',
            'stock__minimum_stock',
            'stock__rack',
            'stock__tracked',
            'stock__purchase_rate',
            'stock__calculated_price',
            'stock__order_rate',
            'stock__discount_margin',
                'stock__store_point__id',
                'stock__store_point__alias',
                'stock__store_point__name',
                'stock__store_point__phone',
                'stock__store_point__address',
                'stock__store_point__type',
                'stock__store_point__populate_global_product',
                'stock__store_point__auto_adjustment',
                'stock__store_point__created_at',
                'stock__store_point__updated_at',
                'stock__product__id',
                'stock__product__code',
                'stock__product__species',
                'stock__product__alias',
                'stock__product__name',
                'stock__product__strength',
                'stock__product__full_name',
                'stock__product__description',
                'stock__product__trading_price',
                'stock__product__purchase_price',
                'stock__product__status',
                'stock__product__is_salesable',
                'stock__product__is_service',
                'stock__product__is_global',
                'stock__product__conversion_factor',
                'stock__product__category',
                'stock__product__is_printable',
                'stock__product__image',
                'stock__product__order_limit_per_day',
                'stock__product__discount_rate',
                    'stock__product__manufacturing_company__id',
                    'stock__product__manufacturing_company__alias',
                    'stock__product__manufacturing_company__name',
                    'stock__product__manufacturing_company__description',
                    'stock__product__manufacturing_company__is_global',
                    'stock__product__form__id',
                    'stock__product__form__alias',
                    'stock__product__form__name',
                    'stock__product__form__description',
                    'stock__product__form__is_global',
                    'stock__product__subgroup__id',
                    'stock__product__subgroup__alias',
                    'stock__product__subgroup__name',
                    'stock__product__subgroup__description',
                    'stock__product__subgroup__is_global',
                        'stock__product__subgroup__product_group__id',
                        'stock__product__subgroup__product_group__alias',
                        'stock__product__subgroup__product_group__name',
                        'stock__product__subgroup__product_group__description',
                        'stock__product__subgroup__product_group__is_global',
                        'stock__product__subgroup__product_group__type',
                    'stock__product__generic__id',
                    'stock__product__generic__alias',
                    'stock__product__generic__name',
                    'stock__product__generic__description',
                    'stock__product__generic__is_global',
                    'stock__product__category__id',
                    'stock__product__category__alias',
                    'stock__product__category__name',
                    'stock__product__category__description',
                    'stock__product__category__is_global',
                    'stock__product__primary_unit__id',
                    'stock__product__primary_unit__alias',
                    'stock__product__primary_unit__name',
                    'stock__product__primary_unit__description',
                    'stock__product__secondary_unit__id',
                    'stock__product__secondary_unit__alias',
                    'stock__product__secondary_unit__name',
                    'stock__product__secondary_unit__description',
    ).order_by('stock__product_full_name')

    queryset = Purchase.objects.prefetch_related(
        Prefetch('stock_io_logs', queryset=order_items)
    ).filter(
        pk=order_id,
        status=Status.DISTRIBUTOR_ORDER,
        distributor_order_type=DistributorOrderType.ORDER,
        purchase_type=PurchaseType.VENDOR_ORDER,
    ).select_related(
        'distributor',
        'organization',
    ).only(
        'id',
        'alias',
        'status',
        'purchase_date',
        'amount',
        'discount',
        'discount_rate',
        'round_discount',
        'vat_rate',
        'vat_total',
        'tax_rate',
        'tax_total',
        'grand_total',
        'additional_discount',
        'additional_discount_rate',
        'additional_cost',
        'additional_cost_rate',
        'distributor__id',
        'distributor__alias',
        'distributor__name',
        'distributor__status',
        'distributor__address',
        'distributor__primary_mobile',
        'organization__id',
        'organization__alias',
        'organization__name',
        'organization__status',
        'organization__address',
        'organization__primary_mobile',
        'organization__delivery_thana',
        'organization__delivery_sub_area',
    )
    return DistributorOrderDetailsGetForDistributorSerializer(queryset.first()).data

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

def get_area_name(code=''):
    if not code:
        return '-'
    result = list(filter(lambda item: item[0] == code, DhakaThana().choices()))
    return result[0][1] if result else '-'

def prepare_order_data(data):
    import datetime

    date_time_str = data.get('purchase_date')
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S%z')
    data['purchase_date'] = date_time_obj.date()
    return data

def create_barcode_image(string):
    import barcode
    from barcode.writer import ImageWriter
    source = os.path.join(settings.REPO_DIR, "projectile")
    dest = os.path.join(settings.REPO_DIR, "assets")
    code128 = barcode.get('code128', str(string), writer=ImageWriter())
    file = f"{dest}/{string}"
    filename = code128.save(file)
    # os.replace(f"{source}/{filename}", f"{dest}/{filename}")
    return filename

def prepare_context(order_id):
    order_data = get_order(order_id)
    if not order_data:
        return
    distributor = Organization.objects.values(
        'id',
        'name',
        'address',
        'primary_mobile',
        'other_contact',
        'email'
    ).get(pk=order_data.get('distributor').get('id'))
    distributor['contact'] = get_contact(distributor)
    context = {
        "title" : "HealthOS Invoice",
        "header_title": "Invoice",
        "order_data": prepare_order_data(order_data),
        "distributor": distributor,
        "barcode": create_barcode_image(order_id)
    }
    return context

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

def store_invoice(file, order_ids, organization_id, entry_by_id, repeat):
    data_list = []
    with open(file, 'rb') as fi:
        outfile = File(fi, name=os.path.basename(fi.name))
        invoice_storage = InvoiceFileStorage.objects.create(
            content=outfile,
            organization_id=organization_id,
            repeat=repeat,
            entry_by_id=entry_by_id
        )
        invoice_storage.save()
        for order_id in order_ids:
            data_list.append(
                OrderInvoiceConnector(
                    order_id=order_id,
                invoice_id=invoice_storage.id
                )
            )

        OrderInvoiceConnector.objects.bulk_create(data_list)
        if Path(file).is_file():
            os.remove(file)

def merge_pdf(pdfs, order_ids, outfile_name, organization_id, entry_by_id, repeat):
    source = os.path.join(settings.REPO_DIR, "projectile")
    dest = os.path.join(settings.REPO_DIR, "assets")
    merger = PdfFileMerger()
    output_file = outfile_name
    blank_pdf = "blank.pdf"
    HTML(string="").write_pdf(
        blank_pdf
    )

    for index, pdf in enumerate(pdfs):
        pdf_file = PdfFileReader(open(pdf, 'rb'))
        page_count = pdf_file.getNumPages()
        if (page_count % 2) == 0:
            merger.append(pdf)
        else:
            if index == len(pdfs) - 1:
                merger.append(pdf)
            else:
                merger.append(pdf)
                merger.append(blank_pdf)

    merger.write(output_file)
    merger.close()
    if Path(blank_pdf).is_file():
        os.remove(blank_pdf)

    for pdf in set(pdfs):
        if Path(pdf).is_file():
            os.remove(pdf)

    for barcode in order_ids:
        if Path(f"{dest}/{barcode}.png").is_file():
            os.remove(f"{dest}/{barcode}.png")

    store_invoice(output_file, order_ids, organization_id, entry_by_id, repeat)

def create_pdf(order_id):
    """Command runner."""
    template_name = 'projectile/templates/html/invoice.html'
    outfile = f"{order_id}.pdf"
    template_vars = prepare_context(order_id)
    env = Environment(loader=FileSystemLoader('.'))
    env.filters['product_short_name'] = product_short_name
    env.filters['to_barcode'] = to_barcode
    env.filters['get_area_name'] = get_area_name
    template = env.get_template(template_name)
    html_out = template.render(template_vars)
    pdf = makepdf(html_out)
    Path(outfile).write_bytes(pdf)
    organization_id = template_vars.get('distributor').get('id')
    return organization_id

@app.task
def create_pdf_invoice_lazy(order_ids, outfile_name, repeat, entry_by_id=None):
    file_list = []
    for item in order_ids:
        organization_id = create_pdf(item)
        for count in range(0, repeat):
            file_list.append(f"{item}.pdf")

    merge_pdf(file_list, order_ids, outfile_name, organization_id, entry_by_id, repeat)


def create_pdf_invoice(order_ids = [], repeat=3, entry_by_id=None):

    if not order_ids:
        response = {
            'status': 'Failed',
            'message': "Order ids is required"
        }
        return response

    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H%M%S")
    domain = os.environ.get('DOMAIN', 'localhost:8000')
    file_list = []
    chunk_size = 50
    data_length = len(order_ids)
    number_of_operations = int((data_length / chunk_size) + 1)
    lower_limit = 0
    upper_limit = chunk_size
    for _ in range(0, number_of_operations):
        data_limit = order_ids[lower_limit : upper_limit]
        lower_limit = upper_limit
        upper_limit += chunk_size
        if data_limit:
            itr_count = _ + 1
            output_file = f"invoice-{itr_count}-{dt_string}.pdf"
            create_pdf_invoice_lazy.delay(order_ids=data_limit, outfile_name=output_file, repeat=repeat)
            file_list.append(f"https://{domain}/media/contents/invoicefilestorage/{output_file}")


    response = {
        'status': 'Success',
        'file': file_list
    }
    return response