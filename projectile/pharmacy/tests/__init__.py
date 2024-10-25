import random
import factory
from datetime import timezone as DTTZ
from django.utils import timezone

from common.enums import Status, PublishStatus
from core.tests import (
    OrganizationFactory,
    PersonFactory,
    PatientFactory,
    DepartmentFactory,
    EmployeeFactory,
    SupplierFactory,
    PersonOrganizationFactory,
    PersonOrganizationEmployeeFactory,
)
# from account.tests import AccountFactory

from ..models import (
    ProductForm,
    ProductManufacturingCompany,
    ProductGeneric,
    ProductCategory,
    ProductGroup,
    ProductSubgroup,
    Product,
    StorePoint,
    Stock,
    Sales,
    Purchase,
    PurchaseRequisition,
    StockIOLog,
    StockTransfer,
    StockAdjustment,
    EmployeeStorepointAccess,
    Unit,
    EmployeeAccountAccess,
    ProductDisbursementCause,
)
from ..enums import (
    StorePointType,
    StockIOType,
    TransferStatusType,
    ProductGroupType,
)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class StorePointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StorePoint

    name = factory.Faker('company')
    phone = factory.Faker('msisdn')
    description = factory.Faker('first_name')
    type = StorePointType.PHARMACY
    address = factory.Faker('address')
    auto_adjustment = random.choice([True, False])
    organization = factory.SubFactory(OrganizationFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductForm

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductManufacturingCompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductManufacturingCompany

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    status = Status.ACTIVE


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductGenericFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductGeneric

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductCategory

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductGroup

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    type = random.choice(ProductGroupType.get_values())


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductSubGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductSubgroup

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    product_group = factory.SubFactory(ProductGroupFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('first_name')
    strength = factory.Faker('first_name')
    description = factory.Faker('first_name')
    trading_price = random.randint(10, 12)
    purchase_price = random.randint(8, 10)
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
    manufacturing_company = factory.SubFactory(ProductManufacturingCompanyFactory)
    form = factory.SubFactory(ProductFormFactory)
    subgroup = factory.SubFactory(ProductSubGroupFactory)
    generic = factory.SubFactory(ProductGenericFactory)
    status = Status.ACTIVE
    is_salesable = random.choice([True, False])
    is_service = random.choice([True, False])
    is_printable = random.choice([True, False])
    primary_unit = factory.SubFactory('pharmacy.tests.UnitFactory')
    secondary_unit = factory.SubFactory('pharmacy.tests.UnitFactory')
    conversion_factor = round(random.uniform(0.15, 5.00), 2)
    category = factory.SubFactory(ProductCategoryFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class StockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stock

    organization = factory.SubFactory(OrganizationFactory)
    store_point = factory.SubFactory(StorePointFactory)
    product = factory.SubFactory(ProductFactory)
    stock = random.randint(2000, 10000)
    minimum_stock = random.randint(2000, 10000)
    status = Status.ACTIVE
    auto_adjustment = random.choice([True, False])
    discount_margin = random.choice([True, False])


# pylint: disable=no-init, old-style-class, too-few-public-methods
class ProductWithStockFactory(ProductFactory):
    stock = factory.RelatedFactory(StockFactory, 'product')


# pylint: disable=no-init, old-style-class, too-few-public-methods
class SalesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sales

    organization = factory.SubFactory(OrganizationFactory)
    status = Status.ACTIVE
    sale_date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    buyer = factory.SubFactory(PatientFactory)
    patient_admission = factory.SubFactory('clinic.tests.PatientAdmissionFactory')
    prescription = factory.SubFactory('prescription.tests.PrescriptionFactory')
    amount = random.randint(500, 1000)
    discount = random.randint(10, 100)
    salesman = factory.SubFactory(EmployeeFactory)
    remarks = factory.Faker('first_name')
    transport = random.randint(10, 15)
    organization_department = factory.SubFactory(
        'clinic.tests.OrganizationDepartmentFactory',)
    store_point = factory.SubFactory(StorePointFactory)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class PurchaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Purchase

    organization = factory.SubFactory(OrganizationFactory)
    status = random.choice([0, 2])
    purchase_date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    requisition_date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    receiver = factory.SubFactory(EmployeeFactory)
    department = factory.SubFactory(DepartmentFactory)
    amount = random.randint(500, 1000)
    discount = random.randint(10, 50)
    vat_rate = random.randint(1, 50)
    tax_rate = random.randint(1, 50)
    supplier = factory.SubFactory(SupplierFactory)
    remarks = factory.Faker('first_name')
    transport = random.randint(10, 15)
    is_sales_return = random.choice([True, False])


# pylint: disable=no-init, old-style-class, too-few-public-methods
class StockIOLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockIOLog

    organization = factory.SubFactory(OrganizationFactory)
    stock = factory.SubFactory(StockFactory)
    quantity = random.randint(1, 2)
    rate = random.randint(10, 15)
    batch = factory.Faker('first_name')
    expire_date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    type = StockIOType.INPUT
    sales = factory.SubFactory(SalesFactory)
    purchase = factory.SubFactory(PurchaseFactory)
    status = Status.ACTIVE
    primary_unit = factory.SubFactory('pharmacy.tests.UnitFactory')
    secondary_unit = factory.SubFactory('pharmacy.tests.UnitFactory')
    conversion_factor = round(random.uniform(0.15, 5.00), 2)


# pylint: disable=no-init, old-style-class, too-few-public-methods
class StockTransferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockTransfer

    organization = factory.SubFactory(OrganizationFactory)
    date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    transfer_from = factory.SubFactory(StorePointFactory)
    transfer_to = factory.SubFactory(StorePointFactory)
    by = factory.SubFactory(EmployeeFactory)
    received_by = factory.SubFactory(EmployeeFactory)
    transport = random.randint(10, 15)
    status = random.choice([0, 3])
    remarks = factory.Faker('first_name')
    transfer_status = random.choice(TransferStatusType.get_values())


# pylint: disable=no-init, old-style-class, too-few-public-methods
class StockAdjustmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockAdjustment

    organization = factory.SubFactory(OrganizationFactory)
    date = factory.Faker('date_time', tzinfo=DTTZ.utc)
    store_point = factory.SubFactory(StorePointFactory)
    employee = factory.SubFactory(EmployeeFactory)
    patient = factory.SubFactory(PatientFactory)
    person_organization_patient = factory.SubFactory(PersonOrganizationFactory)
    person_organization_employee = factory.SubFactory(PersonOrganizationFactory)
    is_product_disbrustment = random.choice([True, False])
    remarks = factory.Faker('first_name')
    patient_admission = factory.SubFactory('clinic.tests.PatientAdmissionFactory')


class EmployeeStorepointAccessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployeeStorepointAccess

    employee = factory.SubFactory(EmployeeFactory)
    person_organization = factory.SubFactory(PersonOrganizationEmployeeFactory)
    store_point = factory.SubFactory(StorePointFactory)
    access_status = random.choice([True, False])


# pylint: disable=no-init, old-style-class, too-few-public-methods
class UnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Unit

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)


class EmployeeAccountAccessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployeeAccountAccess

    employee = factory.SubFactory(EmployeeFactory)
    person_organization = factory.SubFactory(PersonOrganizationFactory)
    account = factory.SubFactory('account.tests.AccountFactory')
    access_status = random.choice([True, False])
    organization = factory.SubFactory(OrganizationFactory)


class PurchaseRequisitionFactory(factory.django.DjangoModelFactory):
    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PurchaseRequisition

    purchase = factory.SubFactory(PurchaseFactory)
    requisition = factory.SubFactory(PurchaseFactory)


class ProductDisbursementCauseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductDisbursementCause

    name = factory.Faker('first_name')
    description = factory.Faker('first_name')
    is_global = PublishStatus.PRIVATE
    organization = factory.SubFactory(OrganizationFactory)
