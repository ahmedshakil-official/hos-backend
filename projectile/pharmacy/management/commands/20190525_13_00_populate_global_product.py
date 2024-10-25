import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import IntegrityError
from common.helpers import (
    get_json_data_from_file,
    get_or_create_global_object as product_creator,
    get_or_create_object
)

from pharmacy.models import (
    ProductForm, ProductManufacturingCompany,
    ProductGeneric, ProductGroup, ProductSubgroup,
    Product, Unit, ProductAdditionalInfo
)
from common.enums import Status, PublishStatus
from pharmacy.enums import GlobalProductCategory
logger = logging.getLogger(__name__)


def convert_search_param(search_text):
    if search_text == "" or search_text is None:
        return None
    search_param = search_text
    search_param = search_param.lower()
    search_param = search_param.replace(" ", "").replace("\t", "")
    search_param = search_param.replace("limited.", "limited").replace(
        "limited", "ltd.").replace("ltd.", "ltd")
    return search_param


def get_or_create_global_object(model_name, attribute, case_insensetive_attribute=None, case_insensetive_value=None):

    attribute.pop(case_insensetive_attribute, None)

    queryset = model_name.objects.filter(
        Q(is_global=PublishStatus.INITIALLY_GLOBAL) | Q(
            is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
        status=Status.ACTIVE,
        **attribute
    )

    obj = None
    if case_insensetive_attribute is not None:
        for item in list(queryset):
            converted_search_param = convert_search_param(item.name)
            converted_case_insensetive_value = convert_search_param(
                case_insensetive_value)

            if converted_case_insensetive_value is None:
                return None
            if converted_search_param == converted_case_insensetive_value:
                obj = queryset.filter(pk=item.id).first()
                break

    if obj is None:
        try:
            attribute.update({
                case_insensetive_attribute: case_insensetive_value
            })
            obj = model_name.objects.create(
                status=Status.ACTIVE,
                is_global=PublishStatus.INITIALLY_GLOBAL,
                **attribute
            )
            obj.save()
        except (AssertionError, IntegrityError):
            return None

    return obj


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("IMPORTING PRODUCT")
        products = get_json_data_from_file('tmp/global_product_setb.json')

        group = get_or_create_global_object(
            ProductGroup, {}, 'name', 'Medicine')
        pc_unite = get_or_create_global_object(Unit, {}, 'name', 'Pcs')

        # failed = 0
        for item in tqdm(products):
            data = {}
            brand_name = item['brand_name']
            if item['ext'] is not None:
                brand_name = "{} {}".format(brand_name, item['ext'])

            data.update({'name': brand_name})

            data.update({'form': get_or_create_global_object(
                ProductForm, {}, 'name', item['form'])
            })

            data.update({'manufacturing_company': get_or_create_global_object(
                ProductManufacturingCompany, {}, 'name', item['company_name']
            )})

            data.update({'generic': get_or_create_global_object(
                ProductGeneric, {}, 'name', item['generic_name']
            )})

            data.update({'subgroup': get_or_create_global_object(
                ProductSubgroup, {}, 'name', "n/a"
            )})

            price = 0
            pack_size = 1
            if item['price'] is not None:
                try:
                    price = float(item['price'])
                except ValueError:
                    price = 0

            if item['packssize'] is not None:
                try:
                    pack_size = float(item['packssize'])
                except ValueError:
                    pack_size = 1

            data.update({'trading_price': price})
            data.update({'purchase_price': 0.00})
            data.update({'primary_unit': pc_unite})
            data.update({'secondary_unit': pc_unite})
            data.update({'conversion_factor': 1})
            data.update({'global_category': GlobalProductCategory.GPB})
            data.update({'strength': item['strength']})

            # data.update({'a' : True})

            # data.update({'a' : True})
            item_unite = pc_unite
            if item['unite'] is not None:
                item_unite = get_or_create_global_object(
                    Unit, {}, 'name', item['unite']
                )

            if pack_size == 1:
                if item['unite'] is not None:
                    # this case is when packsize 1 we dont care about unite
                    # print "no secendery unit needed"
                    # set item['unite'] as primary unit & secondery unit with factor 1
                    data.update({'primary_unit': pc_unite})
                    pass

                if item['unite'] is None:
                    # this case is when packsize 1 we dont care about unite
                    # print "no secendery unit needed"
                    # set "Pcs" as primary unit & secondery unit with factor 1
                    pass

            elif pack_size > 1 and item['unite'] is not None:

                # this case is when packsize is greater then 1, we must check what is unit,
                # set Pcs as Primary Unit item['unite'] as  secondery unit with factor item['packssize']

                data.update({'primary_unit': pc_unite})
                data.update({'secondary_unit': item_unite})
                data.update({'conversion_factor': pack_size})

                # not setting any trading price for this case as we dont have correct data
                data.update({'trading_price': 0})


            elif item['unite'] is None:
                # print "no secendery unit needed"
                # set Pcs as primary unit & secondery unit with factor 1
                pass

            product = product_creator(Product, data)

            if product is not None:
                additional_data = {
                    'product': product,
                    'administration': item['administration'],
                    'precaution': item['precaution'],
                    'indication': item['indication'],
                    'contra_indication': item['contra_indication'],
                    'side_effect': item['side_effect'],
                    'mode_of_action': item['mode_of_action'],
                    'interaction': item['interaction'],
                    'adult_dose': item['adult_dose'],
                    'child_dose': item['child_dose'],
                    'renal_dose':  item['renal_dose']

                }
                additional_info = get_or_create_object(
                    ProductAdditionalInfo, additional_data)
