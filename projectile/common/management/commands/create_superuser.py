from itertools import chain, repeat
from getpass import getpass

from django.core.management.base import BaseCommand
from django.db.models import Q
from common.enums import Status
from core.models import Person, Organization
from core.enums import PersonGroupType


class Command(BaseCommand):

    def get_input(self, prompt_text, error_text, is_optional=False):
        _input = input(f"{prompt_text}\n")
        if not is_optional:
            if not _input:
                self.stdout.write(f"{error_text}")
                _input = self.get_input(prompt_text, error_text, is_optional)
        return _input

    def get_password_input(self):
        _input1 = getpass("Password:\n")
        _input2 = getpass("Enter Password again:\n")
        if _input1 and _input2 and _input1 == _input2:
            return _input1
        else:
            self.stdout.write('Password Mismatch, please enter again.')
            return self.get_password_input()

    def handle(self, *args, **options):
        self.stdout.write('Please Enter following info for creating Super User')
        phone = self.get_input(
            prompt_text="*Phone:",
            error_text="Phone is mandatory"
        )
        email =self.get_input(
            prompt_text="Email(Optional):",
            error_text="Email is optional",
            is_optional=True
        )
        first_name = self.get_input(
            prompt_text="*First Name:",
            error_text="First Name is mandatory"
        )
        last_name = self.get_input(
            prompt_text="*Last Name:",
            error_text="Last Name is mandatory"
        )
        password = self.get_password_input()

        existing_user = Person.objects.filter(
            Q(phone=phone) |
            Q(email=email),
            status=Status.ACTIVE,
            person_group=PersonGroupType.SYSTEM_ADMIN,
        )

        if existing_user.exists():
            self.stdout.write('Phone should be unique')
        else:
            organization = Organization.objects.filter(status=Status.ACTIVE).last()
            user = Person.objects.create(
                phone=phone,
                email=email,
                first_name=first_name,
                last_name=last_name,
                person_group=PersonGroupType.SYSTEM_ADMIN,
                is_staff=True,
                is_active=True,
                is_superuser=True,
                organization=organization
            )
            user.set_password(password)
            user.save()

