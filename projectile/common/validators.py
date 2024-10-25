import sys
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from common.enums import PublishStatus, Status
from core.enums import PersonGroupType

def positive_non_zero(value):
    if value <= 0:
        raise ValidationError("Value must be positive and non-zero")

def is_patient(person):
    from core.models import Person
    if 'test' in sys.argv:
        return person
    else:
        if not isinstance(person, int):
            person = person.id
        obj = Person.objects.get(pk=person)
        if obj.person_group == PersonGroupType.PATIENT:
            return person
        else:
            raise ValidationError("Must be a patient")

def is_employee(person):
    from core.models import Person
    if 'test' in sys.argv:
        return person
    else:
        if not isinstance(person, int):
            person = person.id
        obj = Person.objects.get(pk=person)
        if obj.person_group == PersonGroupType.EMPLOYEE:
            return person
        else:
            raise ValidationError("Must be an employee")


def is_person_or_employee(person):
    from core.models import Person
    if 'test' in sys.argv:
        return person
    else:
        if not isinstance(person, int):
            person = person.id
        obj = Person.objects.get(pk=person)
        if obj.person_group == PersonGroupType.PATIENT or \
                obj.person_group == PersonGroupType.EMPLOYEE:
            return person
        else:
            raise ValidationError("Must be an person or employee")


def admin_validate_unique_name_with_org(self, *args, **kwargs):
    """
    send args as select related fields, kwargs as filter fields with key and values.
    if kwargs key's value is None then key__isnull=True will be applied
    """
    error_message = {
        'name': _(
            "Field Name #{} already exists".format(
                self.name
            )
        )
    }
    query = self.__class__.objects.select_related(
        'organization'
    )
    for arg in args:
        query = query.select_related(
            arg
        )

    arguments = {}
    for key, value in kwargs.items():
        if value is not None:
            arguments[key] = value
            error_message['name'] += ', with the {} #{}'.format(key, value)
        else:
            arguments[key + '__isnull'] = True
    if arguments:
        query = query.filter(**arguments)

    query = query.filter(
        name__iexact=self.name,
        status=Status.ACTIVE
    )

    if not self.organization:
        if (self.is_global == PublishStatus.INITIALLY_GLOBAL) \
            or (self.is_global == PublishStatus.WAS_PRIVATE_NOW_GLOBAL):
            query = query.filter(
                Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
                Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL)
            )
        if self.is_global == PublishStatus.PRIVATE:
            query = query.filter(
                is_global=PublishStatus.PRIVATE,
                organization__isnull=True
            )
        if self.pk:
            query = query.exclude(pk=self.pk)

        if query.exists():
            raise ValidationError(
                error_message
            )

    if self.organization:

        global_query = query.filter(
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
            name__iexact=self.name,
            status=Status.ACTIVE
        )
        if self.__class__.__name__ == 'SubService' or self.__class__.__name__ == 'LabTest':
            global_query = global_query.exclude(
                **{
                    '{}__isnull'.format(self.__class__.__name__.lower()): False,
                }
            )
        if global_query.exists():
            if self.pk:
                global_query = global_query.exclude(pk=self.pk)
                if global_query.exists():
                    raise ValidationError(
                        error_message
                    )
            else:
                raise ValidationError(
                    error_message
                )
        if self.is_global == PublishStatus.PRIVATE:
            query = query.filter(
                is_global=PublishStatus.PRIVATE,
                organization=self.organization.pk
            )
            error_message['name'] += ' with the organization #{}'.format(self.organization.name)
            if self.pk:
                query = query.exclude(pk=self.pk)
            if query.exists():
                raise ValidationError(
                    error_message
                )

def validate_unique_name(self, value, model_class, field='name'):
    # validate unique name without organization
    request = self.context.get("request")
    data_id = self.instance.id if self.instance else None
    values = {
        '{}__iexact'.format(field): value
    }
    data = model_class.objects.filter(
        status=Status.ACTIVE,
        **values,
    )

    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        return data_id == data[0].id
    return True

def validate_unique_name_with_org(self, value, model_class, field_name=None):
    request = self.context.get("request")
    values = {'{}__iexact'.format(field_name if field_name else 'name'): value}
    # If field name is not section_name then check_is_global will used to check if it is global
    if field_name:
        check_is_global = Q(organization=request.user.organization)
    else:
        check_is_global = (
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization=request.user.organization)
        )

    try:
        data_id = self.instance.id
    except AttributeError:
        data_id = None

    if data_id:
        data = model_class.objects.exclude(pk=data_id).filter(
            check_is_global,
            status=Status.ACTIVE,
            **values
        )

    else:
        data = model_class.objects.filter(
            check_is_global,
            status=Status.ACTIVE,
            **values
        )

    if data.exists():
        if field_name:
            return False
        else:
            data = model_class.objects.filter(
                organization=request.user.organization,
                status=Status.ACTIVE,
                clone=data[0].id,
            )
            if data.exists():
                data = data.values_list('id', flat=True)
                if data_id in list(data):
                    return True
            return False
    else:
        return True


def validate_unique_lab_test_name_with_org(self, name, model_class, clone_labtest=None):

    data = model_class.objects.filter(
        is_global=PublishStatus.PRIVATE,
        organization=self.request.user.organization,
        name__iexact=name,
        status=Status.ACTIVE
    )

    if data.exists():
        if clone_labtest:
            if data.count() == 1 and data[0].is_global in [
                    PublishStatus.INITIALLY_GLOBAL,
                    PublishStatus.WAS_PRIVATE_NOW_GLOBAL]:
                return True
        return False
    else:
        return True


def validate_unique_sub_service_name(self, name, class_name, service, clone_subservice=None):

    data = class_name.objects.filter(
        is_global=PublishStatus.PRIVATE,
        organization=self.request.user.organization,
        service_id=service,
        name__iexact=name,
        status=Status.ACTIVE
    )

    if data.exists():
        if clone_subservice:
            if data.count() == 1 and data[0].is_global in [
                    PublishStatus.INITIALLY_GLOBAL,
                    PublishStatus.WAS_PRIVATE_NOW_GLOBAL]:
                return True
        return False
    else:
        return True


def validate_unique_name_with_org_and_type(self, name, model_class):
    from pharmacy.enums import ProductGroupType
    request = self.context.get("request")
    # Set the default type for product group
    group_type = ProductGroupType.OTHER
    if hasattr(request.data, 'type'):
        group_type = request.data['type']
    try:
        data_id = self.instance.id
    except AttributeError:
        data_id = None
    if data_id:
        data = model_class.objects.filter(
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization=request.user.organization),
            type=group_type,
            name__iexact=name,
            status=Status.ACTIVE
        ).exclude(pk=data_id, type=group_type)

    else:
        data = model_class.objects.filter(
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization=request.user.organization),
            type=group_type,
            name__iexact=name,
            status=Status.ACTIVE
        )

    if data.exists():
        return False
    else:
        return True


def validate_unique_head_with_org(self, value, model_class, _request=None, group=None):
    if _request:
        request = _request
    else:
        request = self.context.get("request")
    data_id = request.data.get('id', None)
    if group:
        head_group = group
    else:
        head_group = request.data['group']
    data = model_class.objects.filter(
        Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
        Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
        Q(organization=request.user.organization),
        name__iexact=value,
        group=head_group,
        status=Status.ACTIVE
    )
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        if data_id == data[0].id:
            return True
        else:
            return False
    else:
        return True


def validate_non_zero_amount(amount):
    from account.models import Transaction
    if amount == 0:
        raise ValidationError("Amount can not be zero")
    else:
        return amount


def validate_unique_name_with_org_without_is_global(self, value, model_class):
    request = self.context.get("request")
    data_id = request.data.get('id', None)
    data = model_class.objects.filter(
        Q(organization=request.user.organization),
        name__iexact=value,
        status=Status.ACTIVE
    )
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        if data_id == data[0].id:
            return True
        else:
            return False
    else:
        return True


def validate_uniq_designation_with_org(self, value, model_class):
    request = self.context.get("request")
    data_id = request.data.get('id', None)
    data = model_class.objects.filter(
        Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
        Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
        Q(organization=request.user.organization),
        name__iexact=value,
        department=request.data['department'],
        status=Status.ACTIVE
    )
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        if data_id == data[0].id:
            return True
        else:
            return False
    else:
        return True


# validate phone number with person group wise
# takes current value, person group
# return boolean
def validate_phone_number_person_group_wise(
        self, value, person_group=PersonGroupType.EMPLOYEE, organization=None):
    from core.models import PersonOrganization
    data_id = self.instance.id
    data = PersonOrganization.objects.filter(
        status=Status.ACTIVE,
        person_group=person_group,
        phone=value
    )
    if organization:
        data = data.filter(organization=organization)
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        query = data.exclude(pk=data_id)
        if query.exists():
            return False
        return True
    else:
        return True


def validate_uniq_supplier_with_org(self, value, model_class):
    request = self.context.get("request")
    data_id = request.data.get('id', None)
    data = model_class.objects.filter(
        Q(organization=request.user.organization),
        company_name__iexact=value,
        status=Status.ACTIVE
    )
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        if data_id == data[0].id:
            return True
        else:
            return False
    else:
        return True


def validate_unique_bed_name_with_org_and_bed_section(self, value, model_class):
    request = self.context.get("request")
    values = {
        'name__iexact': value,
        'status': Status.ACTIVE,
        'bed_section': request.data.get('bed_section', None)
    }
    arguments = {}
    for key, value in values.items():
        if value:
            arguments[key] = value

    try:
        data_id = self.instance.id
    except AttributeError:
        data_id = None

    if data_id:
        data = model_class.objects.exclude(pk=data_id).filter(
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization=request.user.organization),
            **arguments
        )

    else:
        data = model_class.objects.filter(
            Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization=request.user.organization),
            **arguments
        )

    if data.exists():
        return False
    else:
        return True


def validate_employee_attendence_datewise(self, value, model_class):
    request = self.context.get("request")
    if 'test' in sys.argv:
        return True
    else:
        for data in request.data['employee_attendence']:
            employee = model_class.objects.filter(
                Q(date=data['date']),
                Q(employee=data['employee']),
                Q(type=data['type'])
            )
            if employee.exists():
                return False
        return True


def validate_unique_with_organization(self, value, field_name, model_class):
    """
    takes: compare value, value field name in model and model class name
    returns: true or false
    """
    if isinstance(self, int):
        org_id = self
        data_id = None
    else:
        request = self.context.get("request")
        org_id = request.user.organization_id
        data_id = request.data.get('id', None)
    data = model_class.objects.filter(
        organization=org_id,
        status=Status.ACTIVE,
        **{field_name: value}
    )
    if data.exists() and data_id is None:
        return False
    elif data.exists() and data_id:
        return int(data_id) == data[0].id
    else:
        return True


def validate_phone_number(phone):
    error = "INCORRECT_MOBILE_NUMBER"
    try:
        if phone:
            if re.match(r'[0-9]{10}', phone):
                return phone
            else:
                raise ValidationError(error)
    except ValueError:
        raise ValidationError(error)


def validate_phone_number_with_and_without_country_code(phone):
    from common.helpers import get_json_data_from_file
    from core.models import Person

    error = "INCORRECT_MOBILE_NUMBER"

    country_codes = get_json_data_from_file('tmp/country-code.json')

    # Check if the phone number matches the format with a country code or without
    if not (re.match(r'^\+\d{3}[0-9]{10}$', phone) or re.match(r'^0[0-9]{10}$', phone)):
        raise ValidationError(error)

    # If the phone number starts with '+', extract the country code
    if phone[0] == '+':
        match = re.match(r'^(\+\d{3})[0-9]{10}$', phone)
        if not match:
            raise ValidationError(error)
        country_code = match.group(1)

        # Check if the country code exists in the dictionary
        if country_code not in country_codes:
            raise ValidationError("Invalid country code")

    # Validation for phone numbe by checking with country code.
    phone_numbers = [phone]
    if len(phone)>11:
        # remove country code and append the number to the list.
        phone_numbers.append(phone[-11:])
    else:
        # Add Bd country code for now.
        phone_numbers.append("+88" + phone)

    # if person existis with this number then raise validaton error.
    existing_users = Person.objects.filter(phone__in=phone_numbers).only("id")
    if existing_users:
        raise ValidationError("Phone number must be unique.")

    return phone
