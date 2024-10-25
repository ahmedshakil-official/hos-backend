import os
import pandas as pd
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from pharmacy.models import Product, ProductGroup, ProductSubgroup

logger = logging.getLogger(__name__)


# Declare a global dictionary to store product group and subgroup id mappings
product_group_name_id_dict = {}
product_sub_group_name_id_dict = {}


def populate_product_groups(product_groups, organization_id):
    logger.info("Populating product groups.")
    for group_name in product_groups:
        product_group, created = ProductGroup.objects.get_or_create(
            name__iexact=group_name,
            organization_id=organization_id,
            defaults={"name": group_name, "organization_id": organization_id},
        )
        product_group_name_id_dict[group_name] = product_group.id

    logger.info("Product group population success!!!")


def prepare_product_subgroups(product_subgroups, organization_id):
    logger.info("Populating product subgroups if not exists")
    for subgroup_group_name in product_subgroups:
        subgroup_name, group_name = subgroup_group_name.split("_")
        _group_id = product_group_name_id_dict.get(group_name, None)

        product_subgroup, created = ProductSubgroup.objects.get_or_create(
            name__iexact=subgroup_name,
            organization_id=organization_id,
            product_group_id=_group_id,
            defaults={
                "name": subgroup_name,
                "organization_id": organization_id,
                "product_group_id": _group_id,
            },
        )

        product_sub_group_name_id_dict[subgroup_group_name] = product_subgroup.id

    logger.info("Populating product subgroups finshed!")


def fix_stock_product_group_sub_group():
    try:
        # Get the path to the current directory
        file_path = os.path.join(settings.REPO_DIR, "tmp/product-categorization.xlsx")

        # Read the Excel file
        excel_data = pd.read_excel(file_path)
        # get all the stock ids from the dataframe
        stocks_ids = excel_data["ID"].to_list()

        # get the unique groups from the dataframe
        product_groups = excel_data["Category"].unique().tolist()

        # Prepare the unique subgroup from data frame
        excel_data["subgroup_group"] = (
            excel_data["Sub Category"] + "_" + excel_data["Category"]
        )
        product_subgroups = excel_data["subgroup_group"].unique().tolist()

        # create a dictionary to keep stock id as key and subgroup_group name as value
        stock_subgroup_dict = {}

        for index, row in excel_data.iterrows():
            stock_subgroup_dict[row["ID"]] = row["subgroup_group"]

        # declare a list of product for bulk update
        product_to_be_updated = []
        organization_id = os.environ.get("DISTRIBUTOR_ORG_ID", 303)

        # Create a dictionary of product group and ids
        populate_product_groups(
            product_groups=product_groups, organization_id=organization_id
        )

        # Create a dictionary of product subgroup mappings
        prepare_product_subgroups(
            product_subgroups=product_subgroups, organization_id=organization_id
        )

        # get all the products from db
        products = (
            Product()
            .get_all_actives()
            .filter(stock_list__in=stocks_ids)
            .values("id", "stock_list", "subgroup_id")
        )

        for product in products:
            stock_id = product.get("stock_list", None)
            subgroup_group_name = stock_subgroup_dict.get(stock_id, None)
            _subgroup_id = product_sub_group_name_id_dict.get(subgroup_group_name, None)
            product_subgroup_id = product.get("subgroup_id", None)
            # if there is a mismatch between product subgroup then update it
            if product_subgroup_id != _subgroup_id:
                product_to_be_updated.append(
                    Product(
                        id=product.get("id"),
                        subgroup_id=_subgroup_id
                    )
                )
        if product_to_be_updated:
            Product.objects.bulk_update(product_to_be_updated, fields=["subgroup_id"])

    except Exception as e:
        logger.info(f"An error occurred: {e}")


class Command(BaseCommand):
    help = "Update Stock information based on product-categorization.xlsx"

    def handle(self, *args, **options):
        """Update product subgroup and group"""
        logger.info("Product subgroup group population started.")
        # call the method to fix mismatch of product group sub group.
        fix_stock_product_group_sub_group()

        logger.info("Product subgroup group population Success.")
