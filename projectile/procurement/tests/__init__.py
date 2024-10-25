import factory
from factory.django import DjangoModelFactory

from django.utils import timezone

from core.tests import (
    OrganizationFactory,
    PersonOrganizationFactory,
    PersonOrganizationContractorFactory,
    PersonOrganizationSupplierFactory,
    ScriptFileStorageFactory,
)

from pharmacy.tests import (
    StockFactory,
    PurchaseFactory,
)

from procurement.models import (
    Procure,
    PurchasePrediction,
    PredictionItem,
    PredictionItemSupplier,
    ProcureItem,
    PredictionItemMark,
    ProcureIssueLog,
    ProcureGroup,
    ProcureReturn,
    ReturnSettlement,
    ProcurePayment,
)

from procurement.models import ProcureStatus as ProcureStatusModel

from procurement.enums import (
    ProcureType,
    ProcureStatus,
    ProcurePlatform,
    PredictionItemMarkType,
    RecommendationPriority,
    ProcureItemType,
    RateStatus,
    ProcureIssueType,
    ReturnReason,
    ReturnCurrentStatus,
    ReturnSettlementMethod,
    ProcurePaymentMethod,
)


class PurchasePredictionFactory(DjangoModelFactory):
    class Meta:
        model = PurchasePrediction

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    label = factory.Faker("sentence")
    prediction_file = factory.SubFactory(ScriptFileStorageFactory)
    is_locked = False


class PredictionItemFactory(DjangoModelFactory):
    class Meta:
        model = PredictionItem

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    stock = factory.SubFactory(StockFactory)
    product_name = factory.Faker("word")
    company_name = factory.Faker("company")
    purchase_prediction = factory.SubFactory(PurchasePredictionFactory)
    mrp = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    sale_price = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    avg_purchase_rate = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    lowest_purchase_rate = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    highest_purchase_rate = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    margin = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    old_stock = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    sold_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    purchase_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    short_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    return_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    new_stock = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    prediction = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    new_order = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    suggested_purchase_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    suggested_min_purchase_quantity = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    has_min_purchase_quantity = False  # set false by default
    purchase_order = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    marked_status = factory.Faker(
        "random_element", elements=[PredictionItemMarkType.UN_MARK]
    )
    real_avg = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    assign_to = factory.SubFactory(PersonOrganizationFactory)
    sale_avg_3d = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    worst_rate = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    index = factory.Faker("pyint")


class PredictionItemSupplierFactory(DjangoModelFactory):
    class Meta:
        model = PredictionItemSupplier

    organization = factory.SubFactory(OrganizationFactory)
    prediction_item = factory.SubFactory(PredictionItemFactory)
    # supplier = factory.SubFactory(PersonOrganizationFactory)
    supplier = factory.SubFactory(PersonOrganizationSupplierFactory)
    rate = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    quantity = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    priority = factory.Faker("random_element", elements=[RecommendationPriority.OTHER])


class ProcureFactory(DjangoModelFactory):
    class Meta:
        model = Procure

    date = timezone.now()
    organization = factory.SubFactory(OrganizationFactory)
    supplier = factory.SubFactory(PersonOrganizationSupplierFactory)
    contractor = factory.SubFactory(PersonOrganizationContractorFactory)
    sub_total = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    discount = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    employee = factory.SubFactory(PersonOrganizationFactory)
    type = factory.Faker("random_element", elements=[ProcureType.DEFAULT])
    operation_start = factory.Faker("date_time")
    operation_end = factory.Faker("date_time")
    remarks = factory.Faker("sentence")
    invoices = factory.Faker("sentence")
    geo_location_data = factory.Faker("json")
    requisition = factory.SubFactory(PurchaseFactory)
    # copied_from = factory.SelfAttribute('self')
    current_status = factory.Faker("random_element", elements=[ProcureStatus.DRAFT])
    estimated_collection_time = factory.Faker("date_time")
    medium = factory.Faker("random_element", elements=[ProcurePlatform.PHYSICAL])
    shop_name = factory.Faker("name")
    # procure_group = factory.SubFactory(ProcureGroupFactory)
    credit_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    paid_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    is_credit_purchase = factory.Faker("boolean")
    credit_payment_term = factory.Faker("pyint")
    credit_payment_term_date = factory.Faker("date")
    credit_cost_percentage = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    credit_cost_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    open_credit_balance = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )


class ProcureStatusFactory(DjangoModelFactory):
    class Meta:
        model = ProcureStatusModel

    date = factory.Faker("date_time")
    current_status = factory.Faker("random_element", elements=[ProcureStatus.DRAFT])
    procure = factory.SubFactory(ProcureFactory)
    remarks = factory.Faker("sentence")


class ProcureItemFactory(DjangoModelFactory):
    class Meta:
        model = ProcureItem

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    stock = factory.SubFactory(StockFactory)
    product_name = factory.Faker("word")
    company_name = factory.Faker("company")
    rate = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    quantity = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    type = factory.Faker("random_element", elements=[ProcureItemType.IN])
    procure = factory.SubFactory(ProcureFactory)
    prediction_item = factory.SubFactory(PredictionItemFactory)
    rate_status = factory.Faker("random_element", elements=[RateStatus.OK])


class ProcureIssueLogFactory(DjangoModelFactory):
    class Meta:
        model = ProcureIssueLog

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    supplier = factory.SubFactory(PersonOrganizationFactory)
    employee = factory.SubFactory(PersonOrganizationFactory)
    type = factory.Faker("random_element", elements=[ProcureIssueType.OTHER])
    stock = factory.SubFactory(StockFactory)
    prediction_item = factory.SubFactory(PredictionItemFactory)
    remarks = factory.Faker("sentence")
    geo_location_data = factory.Faker("json")


class PredictionItemMarkFactory(DjangoModelFactory):
    class Meta:
        model = PredictionItemMark

    prediction_item = factory.SubFactory(PredictionItemFactory)
    organization = factory.SubFactory(OrganizationFactory)
    supplier = factory.SubFactory(PersonOrganizationFactory)
    rate = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    type = factory.Faker("random_element", elements=[PredictionItemMarkType.MARK])
    employee = factory.SubFactory(PersonOrganizationFactory)
    remarks = factory.Faker("sentence")


class ProcureGroupFactory(DjangoModelFactory):
    class Meta:
        model = ProcureGroup

    date = factory.Faker("date_time")
    supplier = factory.SubFactory(PersonOrganizationSupplierFactory)
    contractor = factory.SubFactory(PersonOrganizationContractorFactory)
    total_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    total_discount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    num_of_boxes = factory.Faker("pyint")
    num_of_unique_boxes = factory.Faker("pyint")
    current_status = factory.Faker("random_element", elements=[ProcureStatus.DRAFT])
    requisition = factory.SubFactory(PurchaseFactory)


class ProcureReturnFactory(DjangoModelFactory):
    class Meta:
        model = ProcureReturn

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    reason = factory.Faker("random_element", elements=[ReturnReason.OTHER])
    reason_note = factory.Faker("sentence")
    procure = factory.SubFactory(ProcureFactory)
    product_name = factory.Faker("name")
    total_return_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    total_settled_amount = factory.Faker(
        "pydecimal", left_digits=5, right_digits=3, positive=True
    )
    current_status = factory.Faker(
        "random_element", elements=[ReturnCurrentStatus.PENDING]
    )
    settlement_method = factory.Faker(
        "random_element", elements=[ReturnSettlementMethod.CHEQUE]
    )
    full_settlement_date = factory.Faker("date_time")
    employee = factory.SubFactory(PersonOrganizationFactory)
    contractor = factory.SubFactory(PersonOrganizationFactory)
    stock = factory.SubFactory(StockFactory)
    quantity = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    rate = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)


class ReturnSettlementFactory(DjangoModelFactory):
    class Meta:
        model = ReturnSettlement

    procure_return = factory.SubFactory(ProcureReturnFactory)
    date = factory.Faker("date_time")
    settlement_method = factory.Faker(
        "random_element", elements=[ReturnSettlementMethod.CASH]
    )
    settlement_method_reference = factory.Faker("name")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    employee = factory.SubFactory(PersonOrganizationFactory)


class ProcurePaymentFactory(DjangoModelFactory):
    class Meta:
        model = ProcurePayment

    date = factory.Faker("date_time")
    organization = factory.SubFactory(OrganizationFactory)
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=3, positive=True)
    method = factory.Faker("random_element", elements=[ProcurePaymentMethod.CASH])
    method_reference = factory.Faker("sentence")
    procure = factory.SubFactory(ProcureFactory)
