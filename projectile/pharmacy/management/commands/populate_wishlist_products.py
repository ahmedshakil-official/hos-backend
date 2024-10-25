import logging, os
from tqdm import tqdm
import re
import pandas as pd
from validator_collection import checkers
from django_elasticsearch_dsl.signals import RealTimeSignalProcessor
from django_elasticsearch_dsl.apps import DEDConfig
from IPython.display import display

from django.core.management.base import BaseCommand
from django.db.models import F, Func, Value, TextField, Q, signals
from django.db.models.functions import Lower, Replace, Trim, Concat
from django.apps import apps

from common.enums import Status, PublishStatus
from common.helpers import get_or_create_global_object
from pharmacy.models import (
    Product,
    ProductForm,
    ProductManufacturingCompany,
    ProductGeneric,
    ProductAdditionalInfo,
    Stock,
)
from pharmacy.signals import pre_save_stock


logger = logging.getLogger(__name__)
distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

# the regex
pattern_name_strength_fix = Value(r'(?i)(\(\s*MRP\s*\d+(?:\.\d+)?\s*\)|\(\s*\d+\s*(Pcs|Box|ml|Strip|Tab)\s*\))|\d+\s*(Pcs|Strip|Box|bottle)|\(\s*(Cap|cream|oint|strip|pot|Zenith|Albion|Central|inj|APC|Bengal|Mystic|Pharmik|Pristine|Bristol|Tablet|Sugar Free|Suspention|Syrup|Belsen|off|Novo|crm|gel|tab|Cosmic|MedRX|Ibn SIna|Navana|Medimet|Clonazepam|Strips)\)|none|injectin|pot|Oral Solution|Paediatric|vegacap|Suspension|off|PFS|metered')
patternt_remove_space = Value(r'\s+')
# replacement string
replacement = Value(r'')
# regex flags
flags = Value('g')


def get_non_spaced_lower(string):
    if not string:
        string = ""
    return ''.join(string.split()).lower()

def get_brand_name_removing_digit(brand_name):
    result = re.sub("(\s\d+$)|Metered Dose|Convicap|(\s\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", "", brand_name)
    return " ".join(result.split())

def get_brand_name_removing_digit_fraction(brand_name):
    result = re.sub("(\s\d+(?:\.\d+)?$)", "", brand_name)
    return " ".join(result.split())

def get_brand_name_removing_any_digit(brand_name):
    result = re.sub("(\s\d+(?:\.\d+)?)", "", brand_name)
    return " ".join(result.split())

def get_filtered_pack_size(pack_size):
    result = re.sub("(?i)bot|tube|drop|pack|botle", "", pack_size)
    return " ".join(result.split())

def get_string_removing_hyphen(string):
    result = re.sub("-", "", string)
    return " ".join(result.split())

def get_swapped_sterngth(strength):
    split_data = strength.split('+')
    if len(split_data) == 2:
        return f"{split_data[1]} + {split_data[0]}"
    return strength

def get_strength_removing_mg_mcg(strength):
    result = re.sub("mg|mcg|ml|g|u.i.|ui|i.u.|iu", "", strength)
    return " ".join(result.split())

def get_sterngth_fixing_plus_slash(strength):
    split_data = strength.split('+')
    if len(split_data) == 2:
        return f"{get_strength_removing_mg_mcg(split_data[0])}/{get_strength_removing_mg_mcg(split_data[1])}"
    return strength

def get_strength_ignoring_slash(strength):
    split_data = strength.split('/')
    if len(split_data) == 2:
        return f"{split_data[0]}"
    return strength

def get_strength_ignoring_plus(strength):
    split_data = strength.split('+')
    if len(split_data) == 2:
        return f"{split_data[0]}"
    return strength

def get_existing_products_from_db_as_df():

    existing_products = Product.objects.filter(
        status=Status.ACTIVE,
        organization__id=distributor_id
    ).annotate(
        possible_correct_name=Func(
            F('name'),
            pattern_name_strength_fix, replacement, flags,
            function='REGEXP_REPLACE',
            output_field=TextField(),
        ),
        possible_correct_strength=Func(
            F('strength'),
            pattern_name_strength_fix, replacement, flags,
            function='REGEXP_REPLACE',
            output_field=TextField(),
        ),
        possible_correct_full_name=Concat(
            'possible_correct_name',
            'possible_correct_strength'
        ),
        lowered_nospace_possible_correct_full_name=Lower(Trim(
            Func(
                F('possible_correct_full_name'),
                patternt_remove_space, replacement, flags,
                function='REGEXP_REPLACE',
                output_field=TextField(),
            )
        )),
    )
    existing_products_df = pd.DataFrame(
        list(existing_products.values(
            'possible_correct_name',
            'possible_correct_strength',
            'possible_correct_full_name',
            'lowered_nospace_possible_correct_full_name',
        ))
    )
    existing_products_df = existing_products_df.fillna("")
    col_list = existing_products_df.possible_correct_full_name.values.tolist()
    existing_products_df['possible_correct_name_removing_digit'] = existing_products_df['possible_correct_name'].apply(lambda value: get_non_spaced_lower(get_brand_name_removing_any_digit(value)))
    existing_products_df['possible_correct_name_removing_digit_full_name'] = existing_products_df['possible_correct_name_removing_digit'] + existing_products_df['possible_correct_strength']
    existing_products_df['possible_correct_name_removing_digit_full_name'] = existing_products_df['possible_correct_name_removing_digit_full_name'].apply(lambda value: get_non_spaced_lower(value))
    existing_products_df['possible_correct_full_name_removing_hyphen'] = existing_products_df['lowered_nospace_possible_correct_full_name'].apply(lambda value: get_string_removing_hyphen(value))
    existing_products_df['possible_correct_full_name_removing_mg_mcg'] = existing_products_df['lowered_nospace_possible_correct_full_name'].apply(lambda value: get_strength_removing_mg_mcg(value))
    existing_products_df['possible_correct_full_name_ignoring_after_slash'] = existing_products_df['possible_correct_name_removing_digit_full_name'].apply(lambda value: get_strength_ignoring_slash(value))
    return existing_products_df

# Product forms
product_forms = ProductForm.objects.filter(
    Q(organization__id=distributor_id) |
    Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
    Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
    status=Status.ACTIVE
).values(
    "id",
    "name"
)
product_form_df = pd.DataFrame(
    list(product_forms)
)
product_form_df['non_spaced_lower_name'] = product_form_df['name'].apply(lambda value: get_non_spaced_lower(value))

def get_or_create_product_form(name):
    non_spaced_lower_name = get_non_spaced_lower(name)
    product_form_exists = product_form_df.loc[
        (product_form_df.name == name) |
        (product_form_df.non_spaced_lower_name == non_spaced_lower_name)
    ]
    if not product_form_exists.empty:
        existing_product_form = product_form_exists.head(1)
        return int(existing_product_form["id"].to_string(index=False))
    else:
        product_form_instance = ProductForm.objects.create(
            name=name,
            organization_id=distributor_id
        )
        row, col = product_form_df.shape
        product_form_df.loc[row] = {
            "name": name,
            "id": product_form_instance.id,
            "non_spaced_lower_name": get_non_spaced_lower(name)
        }
        return product_form_instance.id

# Product Company
product_companies = ProductManufacturingCompany.objects.filter(
    Q(organization__id=distributor_id) |
    Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
    Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
    status=Status.ACTIVE
).values(
    "id",
    "name"
)
product_company_df = pd.DataFrame(
    list(product_companies)
)
product_company_df['non_spaced_lower_name'] = product_company_df['name'].apply(lambda value: get_non_spaced_lower(value))
def get_or_create_product_company(name):
    non_spaced_lower_name = get_non_spaced_lower(name)
    product_company_exists = product_company_df.loc[
        (product_company_df.name == name) |
        (product_company_df.non_spaced_lower_name == non_spaced_lower_name)
    ]
    if not product_company_exists.empty:
        existing_product_company = product_company_exists.head(1)
        return int(existing_product_company["id"].to_string(index=False))
    else:
        product_company_instance = ProductManufacturingCompany.objects.create(
            name=name,
            organization_id=distributor_id
        )
        row, col = product_company_df.shape
        product_company_df.loc[row] = {
            "name": name,
            "id": product_company_instance.id,
            "non_spaced_lower_name": get_non_spaced_lower(name)
        }
        return product_company_instance.id

#  Product Generic
product_generics = ProductGeneric.objects.filter(
    Q(organization__id=distributor_id) |
    Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
    Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
    status=Status.ACTIVE
).values(
    "id",
    "name"
)
product_generic_df = pd.DataFrame(
    list(product_generics)
)
product_generic_df['non_spaced_lower_name'] = product_generic_df['name'].apply(lambda value: get_non_spaced_lower(value))
def get_or_create_product_generic(name):
    non_spaced_lower_name = get_non_spaced_lower(name)
    product_generic_exists = product_generic_df.loc[
        (product_generic_df.name == name) |
        (product_generic_df.non_spaced_lower_name == non_spaced_lower_name)
    ]
    if not product_generic_exists.empty:
        existing_product_generic = product_generic_exists.head(1)
        return int(existing_product_generic["id"].to_string(index=False))
    else:
        product_generic_instance = ProductGeneric.objects.create(
            name=name,
            organization_id=distributor_id
        )
        row, col = product_generic_df.shape
        product_generic_df.loc[row] = {
            "name": name,
            "id": product_generic_instance.id,
            "non_spaced_lower_name": get_non_spaced_lower(name)
        }
        return product_generic_instance.id

def get_digit_from_string(string):
    regex_pattern = re.compile(r"\d+")
    matching_numbers = re.findall(regex_pattern, string)
    if matching_numbers:
        number = float(matching_numbers[0])
    else:
        number = 0
    return number

def get_product_price(price, pack_size):
    if price is not None:
        if checkers.is_numeric(price):
            price = float(price)
        else:
            price = get_digit_from_string(price)
    else:
        price = 0
    pattern = re.compile(r"[0-9]+'s", re.IGNORECASE)
    result = pattern.findall(pack_size)
    if result:
        pack_size_string = result[0]
    else:
        pack_size_string = "1's"
    regex_pattern = re.compile(r"\d+")
    matching_numbers = re.findall(regex_pattern, pack_size_string)
    if matching_numbers:
        _pack_size = float(matching_numbers[0])
    else:
        _pack_size = 1
    return price * _pack_size


class Command(BaseCommand):
    def handle(self, **options):
        # Discount signals and ES
        app_config = apps.get_app_config(DEDConfig.name)
        app_config.signal_processor.teardown()
        signals.pre_save.disconnect(pre_save_stock, sender=Stock)

        logger.info("IMPORTING WISHLIST PRODUCTS....")
        product_additional_info_data = []
        drug_data_file = "tmp/drug_data.csv"
        drug_data_df = pd.read_csv(drug_data_file)
        drug_data_df = drug_data_df.fillna("")
        drug_data_df = drug_data_df.loc[drug_data_df.ignore != 'Yes']
        existing_products_df = get_existing_products_from_db_as_df()
        # drug_data_df = drug_data_df.head(1000)
        create_count = 0
        for index, row in tqdm(drug_data_df.iterrows()):
            brand_name = row.get("brand_name", "")
            strength = row.get("strength", "")
            pack_size = row.get("packsize", "")
            non_spaced_lower_brand_name = get_non_spaced_lower(brand_name)
            non_spaced_lower_strength = get_non_spaced_lower(strength)
            non_spaced_lower_full_name = f"{non_spaced_lower_brand_name}{non_spaced_lower_strength}"
            non_spaced_lower_full_name_with_strength_swap = f"{non_spaced_lower_brand_name}{get_swapped_sterngth(non_spaced_lower_strength)}"
            non_spaced_lower_full_name_with_strength_fixing_plus_slash = f"{non_spaced_lower_brand_name}{get_sterngth_fixing_plus_slash(non_spaced_lower_strength)}"
            non_spaced_lower_full_name_with_strength_ignoring_slash = f"{non_spaced_lower_brand_name}{get_strength_ignoring_slash(non_spaced_lower_strength)}"
            non_spaced_lower_full_name_with_strength_ignoring_plus = f"{non_spaced_lower_brand_name}{get_strength_ignoring_plus(non_spaced_lower_strength)}"
            non_spaced_lower_full_name_with_strength_ignoring_unit = f"{non_spaced_lower_brand_name}{get_strength_removing_mg_mcg(get_strength_ignoring_slash(non_spaced_lower_strength))}"
            non_spaced_lower_full_name_pack_size = f"{non_spaced_lower_brand_name}{get_non_spaced_lower(get_filtered_pack_size(pack_size))}"
            removing_digit_from_brand_name = get_brand_name_removing_digit(brand_name)
            non_spaced_lower_removing_digit_from_brand_name = get_non_spaced_lower(removing_digit_from_brand_name)
            non_spaced_lower_removing_digit_fraction_from_brand_name = get_non_spaced_lower(get_brand_name_removing_digit_fraction(brand_name))
            non_spaced_lower_removing_digit_from_brand_name_full_name = f"{non_spaced_lower_removing_digit_from_brand_name}{non_spaced_lower_strength}"
            non_spaced_lower_removing_digit_from_brand_name_full_name_with_strength_swap = f"{non_spaced_lower_removing_digit_from_brand_name}{get_swapped_sterngth(non_spaced_lower_strength)}"
            non_spaced_lower_removing_digit_fraction_from_brand_name_full_name = f"{non_spaced_lower_removing_digit_fraction_from_brand_name}{get_swapped_sterngth(non_spaced_lower_strength)}"
            non_spaced_lower_removing_digit_fraction_from_brand_name_full_name_with_strength_swap = f"{non_spaced_lower_removing_digit_fraction_from_brand_name}{get_swapped_sterngth(non_spaced_lower_strength)}"
            non_spaced_lower_removing_any_digit_from_brand_name_full_name = f"{get_non_spaced_lower(get_brand_name_removing_any_digit(brand_name))}{non_spaced_lower_strength}"

            product_exists = existing_products_df.loc[
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_full_name) |
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_full_name_with_strength_ignoring_slash) |
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_full_name_with_strength_ignoring_plus) |
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_full_name_pack_size) |
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_removing_digit_fraction_from_brand_name_full_name) |
                (existing_products_df.possible_correct_name_removing_digit_full_name == non_spaced_lower_removing_digit_fraction_from_brand_name_full_name) |
                (existing_products_df.possible_correct_full_name_removing_hyphen == non_spaced_lower_full_name) |
                (existing_products_df.possible_correct_full_name_removing_hyphen == non_spaced_lower_full_name_pack_size) |
                (existing_products_df.possible_correct_name_removing_digit_full_name == non_spaced_lower_removing_digit_from_brand_name_full_name) |
                (existing_products_df.lowered_nospace_possible_correct_full_name == non_spaced_lower_full_name_with_strength_swap) |
                (existing_products_df.possible_correct_name_removing_digit_full_name == non_spaced_lower_removing_digit_fraction_from_brand_name_full_name_with_strength_swap) |
                (existing_products_df.possible_correct_full_name_removing_hyphen == non_spaced_lower_full_name_with_strength_swap) |
                (existing_products_df.possible_correct_name_removing_digit_full_name == non_spaced_lower_removing_digit_fraction_from_brand_name_full_name_with_strength_swap) |
                (existing_products_df.possible_correct_name_removing_digit_full_name == get_non_spaced_lower(non_spaced_lower_removing_digit_from_brand_name_full_name_with_strength_swap)) |
                (existing_products_df.possible_correct_full_name_removing_mg_mcg == get_non_spaced_lower(non_spaced_lower_full_name_with_strength_fixing_plus_slash)) |
                (existing_products_df.possible_correct_full_name_removing_mg_mcg == get_non_spaced_lower(non_spaced_lower_full_name_with_strength_ignoring_unit)) |
                (existing_products_df.possible_correct_full_name_ignoring_after_slash == non_spaced_lower_full_name_with_strength_ignoring_slash)
            ]

            if product_exists.empty:
                data = {
                    "name": brand_name,
                    "strength": strength,
                    "pack_size": pack_size,
                    "organization_id": distributor_id,
                    "is_published": True,
                    "is_salesable": False,
                    "order_limit_per_day": 1
                }
                display_name = f"{row.get('form')} {brand_name}"
                if strength:
                    display_name = f"{display_name} {strength}"
                if pack_size:
                    display_name = f"display_name ({pack_size})"
                data.update({"display_name": display_name})
                data.update({
                    "form_id": get_or_create_product_form(row.get("form"))
                })
                data.update({
                    "manufacturing_company_id": get_or_create_product_company(row.get("company_name"))
                })
                data.update({
                    "generic_id": get_or_create_product_generic(row.get("generic_name"))
                })
                data.update({
                    "subgroup_id": 210
                })
                product_price = get_product_price(row.get("price", 0), pack_size)
                data.update({'trading_price': product_price})
                data.update({'purchase_price': product_price})
                data.update({'primary_unit_id': 174})
                data.update({'secondary_unit_id': 174})
                data.update({'conversion_factor': 1})
                product_instance = Product.objects.create(**data)
                additional_data = {
                    'product_id': product_instance.id,
                    'administration': row.get("administration", ""),
                    'precaution': row.get("precaution", ""),
                    'indication': row.get("indication", ""),
                    'contra_indication': row.get("contra_indication", ""),
                    'side_effect': row.get("side_effect", ""),
                    'mode_of_action': row.get("mode_of_action", ""),
                    'interaction': row.get("interaction", ""),
                    'adult_dose': row.get("adult_dose", ""),
                    'child_dose': row.get("child_dose", ""),
                    'renal_dose':  row.get("renal_dose", ""),

                }
                product_additional_info_data.append(
                    ProductAdditionalInfo(**additional_data)
                )
                create_count += 1
        ProductAdditionalInfo.objects.bulk_create(
            product_additional_info_data,
            batch_size=5000
        )
        logger.info(f"{create_count} products created!!!")
        # Re connect Signals
        app_config.signal_processor.setup()
        signals.pre_save.connect(pre_save_stock, sender=Stock)
