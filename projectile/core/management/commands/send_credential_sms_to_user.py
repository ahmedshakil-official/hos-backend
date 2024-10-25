import logging
import random, string
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from common.helpers import generate_phone_no_for_sending_sms, query_yes_no
from common.tasks import send_sms
from core.models import Person
from core.enums import PersonGroupType, OrganizationType

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("This script will send credential sms to user")
        user_phone = input("Enter user mobile:")
        user_phone_1 = "0{}".format(user_phone[-10:])
        user = Person().get_all_actives().filter(
            phone=user_phone,
            person_group=PersonGroupType.EMPLOYEE,
            organization__type=OrganizationType.DISTRIBUTOR_BUYER
        )
        if user.exists():
            pass
        else:
            user = Person().get_all_actives().filter(
                phone=user_phone_1,
                person_group=PersonGroupType.EMPLOYEE,
                organization__type=OrganizationType.DISTRIBUTOR_BUYER
            )
        if user.exists():
            user = user.first()
            url = "https://ecom.healthosbd.com"
            full_name = "{} {}".format(user.first_name, user.last_name)
            phone = generate_phone_no_for_sending_sms(user.phone)
            random_pass = "".join(random.choice(string.digits) for _ in range(6))
            question = "\n\n\nDO YOU WANT TO SEND SMS TO :\n\n {} \n\n OF \n\n {}\n\n".format(
                full_name, user.organization.name)
            if query_yes_no(question, "no"):
                user.password = make_password(random_pass)
                user.save(update_fields=['password'])
                sms_text = "Dear {},\nPlease goto {} and login with following credential.\nPhone: {},\nPassword: {}.".format(
                    full_name, url, user.phone, random_pass
                )
                # Sending sms to client
                send_sms.delay(
                    phone,
                    sms_text,
                    user.organization.id
                )
        else:
            logger.info("No user found with this phone")
