import os
import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import transaction

import pandas as pd

from core.models import Person, PersonOrganization
from projectile.settings import REPO_DIR


logger = logging.getLogger(__name__)


@transaction.atomic
def populate_suppliers_code():
    # Define the file path for the Excel data
    file_path = "tmp/suppliers_unique_code.xlsx"
    file_location = os.path.join(REPO_DIR, file_path)

    if not os.path.exists(file_location):
        logger.error(f"File '{file_path}' does not exist.")
        return

    try:
        # Read the Excel file into a DataFrame
        dtypes = {"Supplier Unique Code": str}
        excel_data = pd.read_excel(file_location, dtype=dtypes)

        # Drop rows with NaN or empty values in 'ID' and 'Supplier Unique Code' columns
        excel_data.dropna(subset=["Id", "Supplier Unique Code"], inplace=True)

        # Get a list of supplier IDs from the Excel data
        suppliers_ids = excel_data["Id"].tolist()

        # Create a dictionary to map 'Id' to 'Supplier Unique Code'
        id_code_dict = dict(zip(excel_data["Id"], excel_data["Supplier Unique Code"]))

        # Fetch Person Organization objects to be updated from the database
        suppliers = PersonOrganization.objects.filter(pk__in=suppliers_ids).only(
            "id", "code", "person_id"
        )

        # Prepare a list of PersonOrganization objects with updated 'code' and related person also
        suppliers_to_be_updated = []
        persons_to_be_updated = []
        for supplier in tqdm(suppliers):
            supplier_code = id_code_dict.get(supplier.id)
            # Update the PersonOrganization object's code
            suppliers_to_be_updated.append(
                PersonOrganization(id=supplier.id, code=supplier_code)
            )
            # Update the related Person object's code
            persons_to_be_updated.append(
                Person(id=supplier.person_id, code=supplier_code)
            )

        # Perform the bulk update to update 'code' values in the PersonOrganization model
        PersonOrganization.objects.bulk_update(suppliers_to_be_updated, ["code"])
        # Perform the bulk update to update 'code' values in the Person model
        Person.objects.bulk_update(persons_to_be_updated, ["code"])

        logger.info(f"{suppliers.count()} Suppliers code updated successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")


class Command(BaseCommand):
    """Management script for updating suppliers code"""

    def handle(self, *args, **options):
        """Entry point for command."""
        logger.info("Management script for populate suppliers code started!")

        # Call the populate function to populate supplier code
        populate_suppliers_code()

        logger.info("Management Script finished!")
