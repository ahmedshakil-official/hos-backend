import factory
import random

from common.enums import Status, PublishStatus

from ..models import (
    Person,
    Organization,
    Department,
    EmployeeDesignation,
    OrganizationSetting,
    GroupPermission,
    PersonOrganization,
    PersonOrganizationGroupPermission,
    ScriptFileStorage,
)
from ..enums import (
    PersonGroupType,
    SalaryDisburseTypes,
    SalaryHeadType,
    SalaryHeadDisburseType,
    Packages,
    EntryMode,
    PatientInfoType,
    FilePurposes,
)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class OrganizationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Organization

    name = factory.Faker('company')
    # slogan = factory.Faker('ssn')
    address = factory.Faker('first_name')
    primary_mobile = factory.Faker('msisdn')
    contact_person = factory.Faker('first_name')
    contact_person_designation = factory.Faker('first_name')
    # email = factory.LazyAttribute(lambda organization: '{}@example.com'.format(organization.slogan))
    email = factory.Faker('email')
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class OrganizationSettingFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = OrganizationSetting

    organization = factory.SubFactory(OrganizationFactory)
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class DesignationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployeeDesignation

    name = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    department = factory.SubFactory(DepartmentFactory)
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PersonFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Person

    nid = factory.Faker('ssn')
    code = factory.Faker('ssn')
    email = factory.LazyAttribute(lambda person: '{}@example.com'.format(person.nid))
    password = factory.PostGenerationMethodCall('set_password', 'testpass')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone = factory.Faker('msisdn')
    person_group = PersonGroupType.OTHER
    organization = factory.SubFactory(OrganizationFactory)
    balance = random.randint(100, 120)
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PatientFactory(PersonFactory):
    person_group = PersonGroupType.PATIENT


# pylint: disable=no-init, old-style-class, too-few-public-methods
class EmployeeFactory(PersonFactory):
    person_group = PersonGroupType.EMPLOYEE


class ReferrerFactory(PersonFactory):
    person_group = PersonGroupType.REFERRER


class SupplierFactory(PersonFactory):
    person_group = PersonGroupType.SUPPLIER
    company_name = factory.Faker('first_name')
    contact_person = factory.Faker('first_name')
    opening_balance = random.randint(100, 120)
    contact_person_number = factory.Faker('msisdn')
    contact_person_address = factory.Faker('first_name')


# pylint: disable=no-init, old-style-class, too-few-public-methods
class GroupPermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupPermission

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PersonOrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonOrganization

    person = factory.SubFactory(EmployeeFactory)
    organization = factory.SubFactory(OrganizationFactory)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('first_name')
    status = Status.ACTIVE

class ServiceProviderFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.SERVICE_PROVIDER
    opening_balance = random.randint(100, 120)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PersonOrganizationPatientFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.PATIENT


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PersonOrganizationEmployeeFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.EMPLOYEE


class PersonOrganizationSupplierFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.SUPPLIER
    company_name = factory.Faker('company')
    contact_person = factory.Faker('name')
    opening_balance = random.randint(100, 120)
    contact_person_number = factory.Faker('msisdn')
    contact_person_address = factory.Faker("sentence")


class PersonOrganizationContractorFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.CONTRACTOR
    company_name = factory.Faker("company")
    contact_person = factory.Faker("name")
    opening_balance = random.randint(100, 120)
    contact_person_number = factory.Faker("msisdn")
    contact_person_address = factory.Faker("sentence")


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PersonOrganizationGroupPermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonOrganizationGroupPermission

    person_organization = factory.SubFactory(PersonOrganizationFactory)
    permission = factory.SubFactory(GroupPermissionFactory)
    status = Status.ACTIVE


class PersonOrganizationReferrerFactory(PersonOrganizationFactory):
    person_group = PersonGroupType.REFERRER


class ScriptFileStorageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScriptFileStorage

    content = factory.django.FileField(filename="example_script.csv")
    name = factory.Faker("word")
    content_type = "csv"
    description = factory.Faker("sentence")
    date = factory.Faker("date")
    purpose = factory.Faker("word")
    file_purpose = FilePurposes.SCRIPT
    data = factory.Faker("json")
    set_stock_from_file = False # set your boolean field as required
