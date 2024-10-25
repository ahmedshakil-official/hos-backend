import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import (
    get_json_data_from_file,
    get_global_active_record,
    query_yes_no
)
from common.enums import Status

from pharmacy.models import (
    ProductManufacturingCompany,
    Product,
)

logger = logging.getLogger(__name__)


def replace_company(new_company, old_company):
    '''
    This method replace  manufacturing company of every products
    '''

    # finding all products that belong to duplicate company
    products = Product.objects.filter(
        manufacturing_company=old_company,
        status=Status.ACTIVE
    )

    question = "Do you want to replace \n`{}`\nwith\n`{}`\n".format(
        old_company, new_company)

    # if this duplicate company have any active product
    if products.exists():
        # prompt user for decision
        if query_yes_no(question, "no"):

            # loop through each duplicate product
            for product in products:
                logger.info("Replacing company of {}".format(
                    product))
                # replace its manufacturing company
                product.manufacturing_company = new_company
                product.save(update_fields=['manufacturing_company'])
        # if user dont want to merge company
        else:
            # ask if s/he want to continue the script or abandon
            if query_yes_no("Do you want to stop the script", "yes"):
                return False
    # no product belongs to this manufacturing company, so we can make this draft
    else:
        old_company.status = Status.INACTIVE
        old_company.save(update_fields=['status'])

    return True


def finding_duplicate_company_list(company):
    '''
    This mehtod make list of all duplicate M.C.
    '''
    duplicate_list = []
    # running loop to collect id of each duplicate `M.C.`
    for index in range(1, 11):
        duplicate_finder = "duplicate_{}".format(index)
        # appending each M.C. name into a list
        if type(company[duplicate_finder]) == int:
            duplicate_list.append(company[duplicate_finder])
    return duplicate_list


def finding_main_company(company):
    '''
    This mehtod find the main valid M.C., what will be
    used to replace all other duplicate M.C.
    '''
    try:
        main_company = ProductManufacturingCompany.objects.get(
            pk=company['id']
        )
        # activating it, in case of its not active
        if main_company.status == Status.INACTIVE:
            main_company.status = Status.ACTIVE
            main_company.save(update_fields=['status'])
        return main_company
    except ProductManufacturingCompany.DoesNotExist:
        pass


class Command(BaseCommand):

    def handle(self, **options):

        companies = get_json_data_from_file('tmp/duplicate_company_list.json')

        # loop through each company
        for company in tqdm(companies):

            duplicate_list = finding_duplicate_company_list(company)

            # if the duplicate list contains any id
            if len(set(duplicate_list)) > 0:

                # finding the valid M.C.
                main_company = finding_main_company(company)

                for duplicate_company_id in duplicate_list:
                    # finding active global company for each id
                    duplicate_active_companies = get_global_active_record(
                        ProductManufacturingCompany,
                        {'pk': duplicate_company_id},
                        False
                    )

                    # if this id belongs to any active golbal manufacturing company
                    if duplicate_active_companies is not None:
                        # finding the duplicate manufacturing company
                        duplicate_company = duplicate_active_companies.first()

                        if not replace_company(main_company, duplicate_company):
                            # if this method return False, that mean user want to stop the execution of script
                            return
