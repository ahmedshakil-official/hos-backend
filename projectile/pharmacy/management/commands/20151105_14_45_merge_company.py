import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import get_json_data_from_file, get_global_active_record
from common.enums import Status

from pharmacy.models import (
    ProductManufacturingCompany,
    Product,
)


logger = logging.getLogger(__name__)




class Command(BaseCommand):

    def handle(self, **options):

        main_companies = get_json_data_from_file('tmp/duplicate_company.json')

        # loop through each company
        for mother_company in tqdm(main_companies):

            # find its duplicate companies
            companies = mother_company['duplicate']

            # take main companies name in a variable
            main_company = mother_company['name']

            # loop throuh each duplicate company
            for duplicate_company in companies:

                # find all product associated with name of a given duplicate company,
                # note this will return a queryset

                products = get_global_active_record(
                    Product,
                    {'manufacturing_company__name': duplicate_company['name']},
                    False
                )

                # find all manufacturing company (duplicate) associated with given name
                # note this will return a queryset

                duplicate_companies = get_global_active_record(
                    ProductManufacturingCompany,
                    {'name': duplicate_company['name']},
                    False
                )

                # find manufacturing company (base) object associated with name of main company
                # note this will return a single object

                correct_company = get_global_active_record(
                    ProductManufacturingCompany,
                    {'name': main_company}
                )

                # loop throuh each product what belongs to a duplicate company
                if products:
                    for item in products:
                        # change the manufactruing company
                        item.manufacturing_company = correct_company
                        item.save()

                # loop throuh each duplicate company object
                if duplicate_companies:
                    for item in duplicate_companies:
                        # change status to draft
                        item.status = Status.DRAFT
                        item.save()
