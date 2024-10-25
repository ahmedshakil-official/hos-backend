import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from pharmacy.models import ProductCategory, Product
from core.models import Organization
from common.enums import Status, PublishStatus



logger = logging.getLogger(__name__)

def add_or_get_product_category(data):
    '''
    This function get the product category object for given data
    if not found its create one ad return
    '''
    try:
        category = ProductCategory.objects.get(**data)
    except ProductCategory.DoesNotExist:
        category = ProductCategory.objects.create(**data)
        category.save()
    return category

def add_product_category():

    logger.info("ADDING PRODUCT CATEGORY")

    # adding a default category, all product will get replaced with this category
    data = { 'name' : 'Other', 'is_global' : PublishStatus.INITIALLY_GLOBAL }
    default_category = add_or_get_product_category(data)

    data['is_global'] = PublishStatus.PRIVATE
    
    for organization in Organization.objects.all():
        data['organization'] = organization
        data['name'] = 'Medical'

        # Adding a Medical product category for all organization
        add_or_get_product_category(data)
        data['name'] = 'General'

        # Adding a General product category for all organization
        add_or_get_product_category(data)
    
    # fetching all product from database
    for product in tqdm(Product.objects.all().exclude(category=default_category)):
        # changing their category to default category
        product.category = default_category
        product.save()


class Command(BaseCommand):
    def handle(self, **options):
        add_product_category()
