import logging
import os
import secrets

from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from tqdm import tqdm
from tabulate import tabulate

from common.enums import Status
from common.helpers import query_yes_no
from core.enums import PersonGroupType
from core.models import PersonOrganization, Person

logger = logging.getLogger("Global Log")


class Command(BaseCommand):
    def get_random_password(self):
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(secrets.choice(allowed_chars) for _ in range(8))

    def build_table(self, obj_to_be_updated):
        cache_keys = []
        for item in tqdm(obj_to_be_updated):
            person = Person.objects.filter(id=item.get("id", None))
            cache_key = f"core_person_profile_details_{item.get('id', '')}"
            cache_keys.append(cache_key)
            person.update(
                password=make_password(item["password"]), updated_at=timezone.now()
            )
        cache.delete_many(cache_keys)
        logger.info("Done!!!")

    def show_table(self, user_filter_data):
        table = []
        obj_to_be_updated = []
        for index, user in enumerate(user_filter_data):
            access_level = ", ".join(
                [
                    str(permission__name)
                    for permission__name in user.group_permission.values_list(
                        "permission__name", flat=True
                    )
                ]
            )
            password = self.get_random_password()
            obj_to_be_updated.append(
                {"id": user.person_id, "password": password})
            table.append(
                [
                    index + 1,
                    user.person.id,
                    user.person.full_name,
                    user.person.phone,
                    password,
                    access_level,
                ]
            )

        logger.info(
            tabulate(
                table,
                headers=["Sl", "ID", "Name", "Phone",
                         "Password", "Access Level"],
                tablefmt="grid",
            )
        )

        return obj_to_be_updated
    
    def show_table_for_all_user_data_who_belong_to_all_non_su_admin(self):
        organization_id = os.environ.get("DISTRIBUTOR_ORG_ID", 303)
        users = (
            PersonOrganization.objects.filter(
                status=Status.ACTIVE,
                person_group__in=[
                    PersonGroupType.MONITOR,
                    PersonGroupType.EMPLOYEE,
                    PersonGroupType.TRADER,
                ],
                organization_id=organization_id,
                group_permission__status=Status.ACTIVE,
            )
            .select_related("person")
            .exclude(person__is_superuser=True)
            .distinct("person_id")
        )
        obj_to_be_updated = self.show_table(users)
        return obj_to_be_updated
    def handle(self, *args, **kwargs):
        logger.info(
            "This script will reset password for users who are EMPLOYEE, MONITOR, TRADER of HealthOS"
        )
        question = "Do you want to reset password for HealthOS users?"
        if not query_yes_no(question, "no"):
            return
        question = "Do you want to reset password for all(y) users or individual user(n)?"
        if not query_yes_no(question, "no"):
            self.show_table_for_all_user_data_who_belong_to_all_non_su_admin()
            self.stdout.write(
                self.style.WARNING(
                    "For individiual- ID, for multiple - ID1,ID2,ID3,..."
                )
            )
            user_input = str(input("Please provide user ID \n"))
            user_input_to_list = user_input.split(",")
            users = (
                PersonOrganization.objects.filter(
                    person_id__in=user_input_to_list,
                    status=Status.ACTIVE,
                )
                .select_related("person")
                .exclude(person__is_superuser=True)
                .distinct("person_id")
            )
            if not users:
                return self.stdout.write(
                    self.style.ERROR(
                        "Operation terminate!!!\n - Are you sure? you provide correct IDs\n - Format should be\n  For individiual- ID, for multiple - ID1,ID2,ID3,..."
                    )
                )
            obj_to_be_updated = self.show_table(users)
            self.build_table(obj_to_be_updated)
            total_successful_operation = users.count()
            return self.stdout.write(self.style.SUCCESS(f"Done!!! Password reset has been done for {total_successful_operation} users"))
        obj_to_be_updated = self.show_table_for_all_user_data_who_belong_to_all_non_su_admin()
        self.build_table(obj_to_be_updated)
