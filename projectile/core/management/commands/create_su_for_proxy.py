import logging, os

from django.core.management.base import BaseCommand
from core.models import Person, PersonOrganization
from core.enums import PersonGroupType

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("Creating Super User for Proxy Communication")
        phone = input("Enter Mobile: ")
        email = input("Enter Email: ")
        password = input("Enter Password: ")
        first_name = "Reporter"
        last_name = "Super Admin"
        organization_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        person_data = {
            "email": email,
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "person_group": PersonGroupType.SYSTEM_ADMIN,
            "is_active": True,
            "is_superuser": True,
            "is_staff": True,
            "organization_id": organization_id
        }
        users = Person.objects.bulk_create(
            [Person(**person_data)]
        )
        users[0].set_password(password)
        users[0].save()
        person_organization_data = {
            "email": email,
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "person_group": PersonGroupType.SYSTEM_ADMIN,
            "person_id": users[0].id,
            "organization_id": organization_id
        }
        po_users = PersonOrganization.objects.bulk_create(
            [PersonOrganization(**person_organization_data)]
        )
