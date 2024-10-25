from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.serializers import (
    ModelSerializer, Serializer, ValidationError,
)
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer

from account.models import TransactionPurchase
from common.serializers import DynamicFieldsModelSerializer
from common.custom_serializer_field import CustomVersatileImageFieldSerializer
from core.models import Department


from core.serializers import (
    SupplierBasicSerializer,
    PersonBasicSerializer,
    DepartmentSerializer,
    PersonOrganizationEmployeeSerializer,
    PersonOrganizationEmployeeLiteSerializer,
    PersonOrganizationEmployeeSerializer,
    PersonOrganizationCommonSerializer,
    PersonOrganizationSupplierSerializer,
    PersonOrganizationLiteSerializer,
)

from account.models import Transaction

from common.enums import Status
from common.utils import re_validate_grand_total
from common.validators import (
    validate_unique_name_with_org_without_is_global,
    validate_unique_name_with_org,
    validate_unique_name_with_org_and_type,
    validate_unique_with_organization,
    validate_phone_number,
)
from common.utils import generate_code_with_hex_of_organization_id

from .utils import (
    construct_product_object_from_dictionary,
    construct_store_point_object_from_dictionary,
    construct_stock_object_from_dictionary,
)
from .enums import StockIOType, PurchaseType, PurchaseOrderStatus, AdjustmentType
from .models import (
    ProductForm,
    ProductManufacturingCompany,
    ProductGeneric,
    ProductGroup,
    ProductSubgroup,
    Product,
    StorePoint,
    Sales,
    Stock,
    StockIOLog,
    Purchase,
    PurchaseRequisition,
    SalesReturn,
    PurchaseReturn,
    StockTransfer,
    StockTransferRequisition,
    StockAdjustment,
    EmployeeStorepointAccess,
    EmployeeAccountAccess,
    Unit,
    StoreProductCategory,
    StockIOLogDisbursementCause,
)
from .custom_serializer.product_disbursement_cause import(
    ProductDisbursementCauseModelSerializer
)

from pharmacy.custom_serializer.store_point import (
    StorePointModelSerializer,
)

from .custom_serializer.product_category import (
    ProductCategoryModelSerializer,
)
from .custom_serializer.product_compartment import ProductCompartmentModelSerializer

# pylint: disable=old-style-class, no-init, R0903, C0111
class UnitSerializer(ModelSerializer):
    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, Unit):
            return value
        else:
            raise ValidationError('YOU_ALREADY_HAVE_A_UNIT_WITH_SAME_NAME')

    class Meta:
        model = Unit
        fields = (
            'id',
            'alias',
            # 'created_at',
            # 'updated_at',
            'name',
            'description'
        )
        read_only_fields = (
            'id',
            'alias',
            'created_at',
            'updated_at'
        )

class UnitMergeSerializer(Serializer):
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(
            status=Status.ACTIVE
        )
    )
    clone_unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(
            status=Status.ACTIVE
        )
    )

    def create(self, validated_data):
        pass


class ProductFormSerializer(ModelSerializer):
    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, ProductForm):
            return value
        else:
            raise ValidationError(
                'YOU_ALREADY_HAVE_A_PRODUCT_FORM_WITH_SAME_NAME')

    class Meta:
        model = ProductForm
        fields = (
            'id',
            'alias',
            'name',
            'description',
            'is_global',
        )


class ProductManufacturingCompanySerializer(ModelSerializer):
    logo = CustomVersatileImageFieldSerializer(
        sizes='logo_images',
        required=False
    )

    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, ProductManufacturingCompany):
            return value
        else:
            raise ValidationError(
                'YOU_ALREADY_HAVE_A_MANUFACTURER_WITH_SAME_NAME')

    class Meta:
        model = ProductManufacturingCompany
        fields = (
            'id',
            'alias',
            'name',
            'logo',
            'description',
            'is_global',
        )


class ProductGenericSerializer(ModelSerializer):
    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, ProductGeneric):
            return value
        else:
            raise ValidationError('YOU_HAVE_ALREADY_A_GENERIC_WITH_SAME_NAME')

    class Meta:
        model = ProductGeneric
        fields = (
            'id',
            'alias',
            'name',
            'description',
            'is_global',
        )


class ProductSubgroupBasicSerializer(ModelSerializer):
    class Meta:
        model = ProductSubgroup
        fields = (
            'id',
            'alias',
            'name',
            'description',
            'product_group',
        )

    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, ProductSubgroup):
            return value
        else:
            raise ValidationError('YOU_HAVE_ALREADY_A_SUBGROUP_WITH_SAME_NAME')


class ProductGroupSerializer(ModelSerializer):
    def validate_name(self, data):
        if validate_unique_name_with_org_and_type(self, data, ProductGroup):
            return data
        else:
            raise ValidationError('YOU_HAVE_ALREADY_A_GROUP_WITH_SAME_NAME')

    logo = CustomVersatileImageFieldSerializer(
            sizes='logo_images',
            required=False
        )

    class Meta:
        model = ProductGroup
        fields = (
            'id',
            'alias',
            'name',
            'description',
            'type',
            'is_global',
            'logo',
        )


class ProductSubgroupSerializer(ModelSerializer):
    product_group = ProductGroupSerializer()

    class Meta:
        model = ProductSubgroup
        fields = (
            'id',
            'alias',
            'name',
            'description',
            'product_group',
            'is_global',
        )


class ProductBasicSerializer(ModelSerializer):
    priority = serializers.IntegerField(write_only=True, required=False)
    is_ad_enabled = serializers.BooleanField(write_only=True, required=False)
    is_salesable = serializers.BooleanField(initial=True)
    is_printable = serializers.BooleanField(initial=True)
    image = serializers.ImageField(required=False, allow_null=True)
    trading_price = serializers.FloatField(validators=[MinValueValidator(0)])
    purchase_price = serializers.FloatField(validators=[MinValueValidator(0)])
    discount_rate = serializers.FloatField(validators=[MaxValueValidator(100)])

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'name',
            'display_name',
            'pack_size',
            'strength',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'priority',
            'is_ad_enabled',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_salesable',
            'is_service',
            'is_printable',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
            'category',
            'code',
            'image',
            'is_published',
            'order_limit_per_day',
            'order_limit_per_day_mirpur',
            'order_limit_per_day_uttara',
            'discount_rate',
            'alias_name',
            'is_queueing_item',
            'order_mode',
            'is_flash_item',
            'unit_type',
            'compartment',
            "minimum_order_quantity",
        )

    def validate_code(self, value):
        if value:
            value = generate_code_with_hex_of_organization_id(
                self.context.get("request"), value)
            if not validate_unique_with_organization(self, value, 'code', Product):
                raise ValidationError('YOU_HAVE_ALREADY_A_SAME_CODE')
        return value

    def create(self, validated_data):
        priority = validated_data.pop("priority", None)
        is_ad_enabled = validated_data.pop("is_ad_enabled", None)

        instance = super().create(validated_data)

        update_fields = {}

        if priority is not None:  # Check for None explicitly
            update_fields["priority"] = priority

        if is_ad_enabled is not None:
            update_fields["is_ad_enabled"] = is_ad_enabled

        if update_fields:
            Stock().get_all_actives().filter(product__id=instance.id).update(**update_fields)

        return instance

    def update(self, instance, validated_data):
        priority = validated_data.pop("priority", None)
        is_ad_enabled = validated_data.pop("is_ad_enabled", None)
        # priority and is_ad_enabled value are removed from the `validated_data` dictionary using the `pop()`
        # method to ensure it doesn't interfere with the update of the Product instance.
        # If priority or is_ad_enabled value are not provided (or is None), the Stock instances are not updated.

        update_fields = {}

        if priority is not None:  # Check for None explicitly
            update_fields["priority"] = priority

        if is_ad_enabled is not None:
            update_fields["is_ad_enabled"] = is_ad_enabled

        if update_fields:
            Stock().get_all_actives().filter(product__id=instance.id).update(**update_fields)

        return super().update(instance, validated_data)


class ProductSerializer(ModelSerializer):
    form = ProductFormSerializer()
    subgroup = ProductSubgroupSerializer()
    generic = ProductGenericSerializer()
    manufacturing_company = ProductManufacturingCompanySerializer()
    primary_unit = UnitSerializer()
    secondary_unit = UnitSerializer()
    compartment = ProductCompartmentModelSerializer.Link()
    category = ProductCategoryModelSerializer.Link()
    image = VersatileImageFieldSerializer(
        sizes="product_images"
    )
    image_url =serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'name',
            'strength',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_salesable',
            'is_service',
            'is_printable',
            'is_global',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
            'category',
            'image',
            'discount_rate',
            'order_limit_per_day',
            'image_url',
            'is_queueing_item',
            'unit_type',
            'compartment',
        )


    def get_image_url(self, _object):
        path = f"{settings.FULL_MEDIA_URL}{_object.image}"
        return path if _object.image else None


class ProductWithoutUnitSerializer(ModelSerializer):
    form = ProductFormSerializer()
    subgroup = ProductSubgroupSerializer()
    generic = ProductGenericSerializer()
    manufacturing_company = ProductManufacturingCompanySerializer()

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'name',
            'strength',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_salesable',
            'is_service',
            'conversion_factor',
        )


class StorePointSerializer(DynamicFieldsModelSerializer):
    def validate_name(self, value):
        if validate_unique_name_with_org_without_is_global(self, value, StorePoint):
            return value
        else:
            raise ValidationError(
                'YOU_HAVE_ALREADY_A_STOREPOINT_WITH_SAME_NAME')

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = StorePoint
        fields = (
            'id',
            'alias',
            'created_at',
            'updated_at',
            'name',
            'phone',
            'address',
            'type',
            'populate_global_product',
        )


class StorePointWithCategorySerializer(ModelSerializer):
    phone = serializers.CharField(
        allow_null=False, validators=[validate_phone_number])
    def validate_name(self, value):
        if validate_unique_name_with_org_without_is_global(self, value, StorePoint):
            return value
        else:
            raise ValidationError(
                'YOU_HAVE_ALREADY_A_STOREPOINT_WITH_SAME_NAME')

    class Meta:
        model = StorePoint
        fields = (
            'id',
            'alias',
            'status',
            'name',
            'phone',
            'address',
            'type',
            'populate_global_product',
            'product_category',
        )


class StoreProductCategorySerializer(ModelSerializer):

    class Meta:
        model = StoreProductCategory
        fields = (
            'id',
            'store_point',
            'product_category',
        )


class StockBasicSerializer(ModelSerializer):
    stock = serializers.FloatField(min_value=0)

    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'store_point',
            'product',
            'display_name',
            'stock',
            'demand',
            'minimum_stock',
            'rack',
            'orderable_stock',
        )


class StockWithStorePointSerializer(StockBasicSerializer):
    store_point = StorePointSerializer()

    # pylint: disable=old-style-class, no-init
    class Meta(StockBasicSerializer.Meta):
        model = Stock
        fields = StockBasicSerializer.Meta.fields + (
            'tracked',
            'discount_margin',
        )

class StockSerializer(ModelSerializer):
    store_point = StorePointSerializer()
    product = ProductWithoutUnitSerializer()
    stock = serializers.FloatField(min_value=0)

    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'store_point',
            'product',
            'stock',
            'ecom_stock',
            'orderable_stock',
            'demand',
            'calculated_price',
            'minimum_stock',
            'rack',
            'purchase_rate',
            'sales_rate',
        )


class StockReportBatchWiseSerializer(Serializer):
    stock = serializers.SerializerMethodField()
    batch = serializers.CharField()
    quantity = serializers.FloatField()
    expire_date = serializers.DateField()
    last_usage = serializers.DateField()

    def get_stock(self, obj):
        return construct_stock_object_from_dictionary(obj)


class StockIOLogForRateSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init
    class Meta:
        model = StockIOLog
        fields = (
            'quantity',
            'rate',
            'conversion_factor',
            'secondary_unit_flag',
        )


class StockWithProductUnitForDetailsSerializer(ModelSerializer):
    store_point = StorePointSerializer()
    product = ProductSerializer()
    stock = serializers.FloatField(min_value=0)
    avg_purchase_price = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'store_point',
            'product',
            'stock',
            'demand',
            'minimum_stock',
            'rack',
            'tracked',
            'calculated_price',
            'purchase_rate',
            'orderable_stock',
            'avg_purchase_price',
        )

    def get_avg_purchase_price(self, obj):
        from pharmacy.helpers import get_average_purchase_price
        view = self.context.get('view', None)
        if not (view and view.__class__.__name__ == "PurchaseRequisitionDetails"):
            return 0
        instance = view.get_object()
        return get_average_purchase_price(obj.id, instance.purchase_date)


class StockWithProductUnitSerializer(StockWithProductUnitForDetailsSerializer):
    log_price = serializers.FloatField(default=0.0)
    latest_purchase_unit = UnitSerializer()
    latest_sale_unit = UnitSerializer()

    # pylint: disable=old-style-class, no-init
    class Meta(StockWithProductUnitForDetailsSerializer.Meta):
        model = Stock
        fields = StockWithProductUnitForDetailsSerializer.Meta.fields + (
            'tracked',
            'sales_rate',
            'purchase_rate',
            'calculated_price',
            'order_rate',
            'log_price',
            'latest_purchase_unit',
            'latest_sale_unit',
        )


class ProductWithStockSerializer(ProductSerializer):
    stock_list = StockBasicSerializer(many=True)
    medicine_name = serializers.CharField(
        source='get_medicine_name', read_only=True)
    category = ProductCategoryModelSerializer.Link()

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'name',
            'display_name',
            'pack_size',
            'strength',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'stock_list',
            'medicine_name',
            'is_salesable',
            'is_service',
            'is_printable',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
            'is_global',
            'category',
            'code',
            'image',
            'is_published',
            'order_limit_per_day',
            'order_limit_per_day_mirpur',
            'order_limit_per_day_uttara',
            'discount_rate',
            'alias_name',
            'is_queueing_item',
            'order_mode',
            'is_flash_item',
            'unit_type',
            'compartment',
            'priority',
            'is_ad_enabled',
            "minimum_order_quantity",
        )


class ProductWithoutStockSerializer(ProductSerializer):
    # pylint: disable=old-style-class, no-init

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'name',
            'strength',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'stock_list',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_global',
            # 'medicine_name',
            'is_salesable',
            'is_service',
            'is_printable',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
            'is_published',
            'is_flash_item',
            'order_mode',
        )


class ProductWithoutStockLiteSerializer(ProductSerializer):

    class Meta:
        model = Product
        fields = (
            'id',
            'alias',
            'created_at',
            'updated_at',
            'name',
            'strength',
            'clone',
            'full_name',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'stock_list',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_published',
            'is_printable',
            'is_global',
            'is_salesable',
            'is_service',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
            'category',
            'priority',
            'is_ad_enabled',
            'order_limit_per_day_mirpur',
            'order_limit_per_day_uttara',
            "minimum_order_quantity",
        )


class PossibleDuplicateProductSerializer(Serializer):
    name = serializers.CharField()
    full_name = serializers.CharField()
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    possible_duplicate = serializers.IntegerField()
    product_id = serializers.IntegerField()
    form_name = serializers.CharField()
    company = serializers.CharField()
    used = serializers.IntegerField()

    def update(self, _object, validated_data):
        pass

    def create(self, _object):
        pass


class StockIOLogDisbursementCauseSerializer(ModelSerializer):
    disbursement_cause = ProductDisbursementCauseModelSerializer.List()
    class Meta:
        model = StockIOLogDisbursementCause
        fields = (
            'id',
            'disbursement_cause',
            'number_of_usage'
        )


class StockIOLogSerializer(ModelSerializer):
    quantity = serializers.FloatField(min_value=0)
    primary_unit = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Unit.objects.filter().only('id')
    )
    secondary_unit = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Unit.objects.filter().only('id')
    )
    # stock = CustomRelatedField(
    #     model=Stock,
    # )

    class Meta:
        model = StockIOLog
        fields = (
            'id',
            'alias',
            'status',
            'stock',
            'quantity',
            'rate',
            'batch',
            'expire_date',
            'date',
            'type',
            'primary_unit',
            'secondary_unit',
            'discount_rate',
            'discount_total',
            'vat_rate',
            'vat_total',
            'tax_total',
            'tax_rate',
            'conversion_factor',
            'secondary_unit_flag',
            'data_entry_status',
            'round_discount',
            'base_discount',
        )


class StockIOLogWithUnitSerializer(StockIOLogSerializer):
    primary_unit = UnitSerializer()
    secondary_unit = UnitSerializer()


class StockIOReportSerializer(Serializer):
    batch = serializers.CharField()
    date = serializers.DateField()
    product_in = serializers.SerializerMethodField()
    product_out = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    sales__alias = serializers.CharField()
    sales__is_purchase_return = serializers.BooleanField()
    purchase__alias = serializers.CharField()
    purchase__is_sales_return = serializers.BooleanField()
    adjustment__alias = serializers.CharField()
    transfer__alias = serializers.CharField()
    adjustment__is_product_disbrustment = serializers.BooleanField()

    def get_stock(self, obj):
        return int(obj['row_total'])

    def get_product_in(self, obj):
        return int(obj['product_in'])

    def get_product_out(self, obj):
        return int(obj['product_out'])


class StockWithProductForRequisitionSerializer(ModelSerializer):
    product = ProductSerializer()
    stocks_io = StockIOLogWithUnitSerializer(many=True)
    stock = serializers.FloatField(min_value=0)
    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'product',
            'stocks_io',
            'order_rate',
            'sales_rate',
            'stock',
            'rack',
            'tracked',
            'purchase_rate',
        )

    def get_latest_order(self, obj):
        serializer = StockIOLogForRateSerializer(
            obj.latest_order[:1], many=True
        )
        return serializer.data


class ProductStockReportSerializer(Serializer):
    stock = serializers.SerializerMethodField()
    sales_sum = serializers.IntegerField()
    purchase_sum = serializers.IntegerField()
    transfer_in = serializers.IntegerField()
    transfer_out = serializers.IntegerField()
    disbursement = serializers.IntegerField()
    adjustment_in = serializers.IntegerField()
    adjustment_out = serializers.IntegerField()

    def get_stock(self, obj):
        return construct_stock_object_from_dictionary(obj)


class WithoutStockIOLogBatchWiseSerializer(ModelSerializer):
    # batch = serializers.SerializerMethodField()
    # quantity = serializers.SerializerMethodField()
    # expire_date = serializers.SerializerMethodField()

    class Meta:
        model = StockIOLog
        fields = (
            'batch',
            'quantity',
            'expire_date',
        )

    # def get_batch(self, obj):
    #     return obj.batch

    # def get_quantity(self, obj):
    #     return obj.qty

    # def get_expire_date(self, obj):
    #     return obj.expire_date


class StockIOLogBatchWiseSerializer(WithoutStockIOLogBatchWiseSerializer):
    # stock = StockSerializer()
    class Meta:
        model = StockIOLog
        fields = WithoutStockIOLogBatchWiseSerializer.Meta.fields + (
            # 'stock',
        )


class StockWithStockBatchSerializer(ModelSerializer):
    stock = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'batch',
            'quantity',
        )

    def get_stock(self, obj):
        return obj.stock.stock

    def get_batch(self, obj):
        return obj.batch

    def get_quantity(self, obj):
        return obj.qty


class StockIOLogBatchWiseDateSerializer(ModelSerializer):
    product = serializers.SerializerMethodField()
    storepoint = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    _total_stocks = []

    class Meta:
        model = StockIOLog
        fields = (
            'product',
            'storepoint',
            'date',
            'stock',
        )

    def get_product(self, obj):
        serializer = ProductWithStockSerializer(obj.stock.product)
        return serializer.data

    def get_storepoint(self, obj):
        serializer = StorePointSerializer(obj.stock.store_point)
        return serializer.data

    def get_date(self, obj):
        return obj.date

    def get_stock(self, obj):
        serializer = StockWithStockBatchSerializer(obj)
        self._total_stocks.append(serializer.data)
        return self._total_stocks


class StockIOLogDetailsSerializer(StockIOLogSerializer):
    stock = StockWithProductUnitForDetailsSerializer()


class StockIOLogDetailsWithUnitDetailsSerializer(StockIOLogSerializer):
    stock = StockWithProductUnitForDetailsSerializer()
    primary_unit = UnitSerializer()
    secondary_unit = UnitSerializer()


class StockIOLogDetailsWithDisbursementCauseSerializer(StockIOLogDetailsSerializer):
    io_log_disbursement_causes = StockIOLogDisbursementCauseSerializer(many=True)
    # pylint: disable=old-style-class, no-init
    class Meta:
        model = StockIOLog
        fields = StockIOLogDetailsSerializer.Meta.fields + (
            'io_log_disbursement_causes',
        )


class StockTransferBasicSerializer(ModelSerializer):
    stock_io_logs = StockIOLogSerializer(many=True, read_only=True)

    class Meta:
        model = StockTransfer
        fields = (
            'id',
            'alias',
            'date',
            'transfer_from',
            'transfer_to',
            'transport',
            'by',
            'person_organization_by',
            'received_by',
            'transfer_status',
            'stock_io_logs',
            'remarks',
        )


class StockTransferLiteSerializer(ModelSerializer):
    transfer_from = StorePointSerializer()
    transfer_to = StorePointSerializer()
    person_organization_by = PersonOrganizationEmployeeLiteSerializer(read_only=True)

    class Meta:
        model = StockTransfer
        fields = (
            'id',
            'alias',
            'date',
            'transfer_from',
            'transfer_to',
            'person_organization_by',
            'remarks',
            'transport',
        )


class StockIOLogTransferSerializer(StockIOLogSerializer):
    # quantity = serializers.IntegerField()
    # batch = serializers.CharField()
    # expire_date = serializers.DateField()
    stock = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.filter())


class StockTransferSerializer(StockTransferBasicSerializer):
    stock_io_logs = StockIOLogTransferSerializer(many=True)

    class Meta:
        model = StockTransfer
        fields = (
            'id',
            'alias',
            'status',
            'date',
            'transfer_from',
            'transfer_to',
            'transport',
            'by',
            'person_organization_by',
            'received_by',
            'person_organization_received_by',
            'stock_io_logs',
            'transfer_status',
            'remarks',
            'copied_from',
        )

    def create(self, validated_data):
        request = self.context.get("request")

        stock_io_logs = validated_data.pop('stock_io_logs', [])

        stock_transfer = StockTransfer.objects.create(
            organization=request.user.organization,
            entry_by=request.user,
            **validated_data
        )

        for item in stock_io_logs:
            # StockTransfer.objects.create(
            #     organization=request.user.organization,
            #     date=validated_data ['date'],
            #     transfer_from=validated_data ['transfer_from'],
            #     transfer_to=validated_data ['transfer_to'],
            #     by=validated_data ['by']
            # )
            stock = item['stock']
            del item['stock']

            StockIOLog.objects.create(
                status=stock_transfer.status,
                transfer=stock_transfer,
                date=stock_transfer.date,
                organization=request.user.organization,
                entry_by=request.user,
                type=StockIOType.INPUT,
                stock=Stock.objects.get(
                    store_point=validated_data['transfer_to'],
                    product=stock.product
                ),
                # quantity=item['quantity'],
                # batch=item['batch'],
                # expire_date=item['expire_date']
                **item
            )

            StockIOLog.objects.create(
                status=stock_transfer.status,
                transfer=stock_transfer,
                date=stock_transfer.date,
                organization=request.user.organization,
                entry_by=request.user,
                type=StockIOType.OUT,
                stock=Stock.objects.get(
                    store_point=validated_data['transfer_from'],
                    product=stock.product
                ),
                # quantity=item['quantity'],
                # batch=item['batch'],
                # expire_date=item['expire_date']
                **item
            )

        return stock_transfer


class StockTransferDetailsSerializer(StockTransferBasicSerializer):
    copied_from = StockTransferBasicSerializer(
        allow_null=True, default=None, many=False)
    transfer_from = StorePointSerializer(read_only=True)
    transfer_to = StorePointSerializer(read_only=True)
    person_organization_by = PersonOrganizationEmployeeLiteSerializer()
    person_organization_received_by = PersonOrganizationEmployeeLiteSerializer()
    stock_io_logs = StockIOLogDetailsWithUnitDetailsSerializer(read_only=True, many=True)

    class Meta:
        model = StockTransfer
        fields = (
            'id',
            'alias',
            'status',
            'date',
            'transfer_from',
            'transfer_to',
            'transport',
            'person_organization_by',
            'person_organization_received_by',
            'status',
            'stock_io_logs',
            'remarks',
            'copied_from',
        )


class StockTransferRequisitionSerializer(ModelSerializer):
    class Meta:
        model = StockTransferRequisition
        fields = (
            'id',
            'requisition',
            'stock_transfer',
            'organization',
            'entry_by',
        )


class PurchaseLiteSerializer(ModelSerializer):
    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'vouchar_no',
            'organization_wise_serial',
        )

class TransactionOrganizationWiseSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id',
            'organization_wise_serial',
        )


class TransactionPurchaseLiteSerializer(ModelSerializer):
    transaction = TransactionOrganizationWiseSerializer(read_only=True)
    class Meta:
        model = TransactionPurchase
        fields = (
            'id',
            'transaction',
            'amount',
        )

class RequsitionLiteSerializerForPurchaseDetailsOrder(ModelSerializer):

    class Meta:
        model = Purchase
        fields = (
            'id',
            'purchase_date',
            'requisition_date',
            'organization_wise_serial',
            'remarks',
        )

        read_only_fields = (
            'id',
            'purchase_date',
            'requisition_date',
            'organization_wise_serial',
            'remarks',
        )


class PurchaseBasicSerializer(ModelSerializer):
    stock_io_logs = StockIOLogSerializer(many=True, read_only=True)
    vat_total = serializers.FloatField(read_only=True)
    tax_total = serializers.FloatField(read_only=True)
    grand_total = serializers.FloatField(read_only=True)
    department = DepartmentSerializer(read_only=True)
    requisitions = RequsitionLiteSerializerForPurchaseDetailsOrder(allow_null=True, many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_order_status',
            'purchase_date',
            'requisition_date',
            'supplier',
            'person_organization_supplier',
            'department',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'receiver',
            'person_organization_receiver',
            'stock_io_logs',
            'remarks',
            'transport',
            'is_sales_return',
            'vouchar_no',
            'organization_department',
            'responsible_employee',
            'organization_wise_serial',
            'requisitions',
        )

        read_only_fields = (
            'organization_wise_serial',
            'requisitions',
        )


class PurchaseSerializer(PurchaseBasicSerializer):
    stock_io_logs = StockIOLogSerializer(many=True)

    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(status=Status.ACTIVE),
        allow_null=True, default=None)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_order_status',
            'purchase_date',
            'requisition_date',
            'supplier',
            'department',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'receiver',
            'person_organization_receiver',
            'person_organization_supplier',
            'stock_io_logs',
            'remarks',
            'vouchar_no',
            'transport',
            'is_sales_return',
            'copied_from',
            'requisitions',
            'patient_admission',
            'store_point',
            'organization_department',
        )

    def validate_grand_total(self, value):
        status = value.get("status", Status.ACTIVE)
        if status != Status.DRAFT:
            sub_total = 0
            # calculate subtotal, vat, discount based on all individual IOLog
            for item in value.get('stock_io_logs', []):
                sub_total += (item.get('rate', 0) * item.get('quantity', 0))
                sub_total += item.get('vat_total', 0)
                sub_total += item.get('tax_total', 0)
                sub_total -= item.get('discount_total', 0)
            # check if calculated total is same as grand_total
            re_validate_grand_total(
                grand_total=float(self.initial_data.get('grand_total', 0)),
                calculated_grand_total=sub_total + value.get('round_discount', 0)
            )

    def validate(self, value):
        amount = value.get('amount', None)
        if amount:
            requisitions = self.initial_data.get('requisitions', None)
            if requisitions:
                try:
                    total = 0
                    flag = 0
                    for item in requisitions:
                        purchase_order = Purchase.objects.only(
                            'purchase_type',
                            'purchase_order_status',
                            'amount',
                        ).get(id=item)
                        if purchase_order.purchase_type == PurchaseType.ORDER \
                                and purchase_order.purchase_order_status == \
                                PurchaseOrderStatus.PENDING:
                            total += purchase_order.amount
                            flag = 1
                    if amount > total and flag == 1:
                        raise ValidationError(
                            {'error': "Purchase amount can't be greater than order amount"})
                except Purchase.DoesNotExist:
                    pass
        self.validate_grand_total(value)
        return value

    def create(self, validated_data):
        request = self.context.get("request")

        stock_io_logs = validated_data.pop('stock_io_logs', [])
        # amount = validated_data.get('amount', [])
        # for item in stock_io_logs:
        #     if 'rate' in item:
        #         total += item['quantity'] * item['rate']
        # if total != amount:
        #     validated_data['amount'] = total

        purchase = Purchase.objects.create(
            organization_id=request.user.organization_id,
            entry_by=request.user,
            **validated_data
        )

        # create stock io logs in reverse order
        for item in reversed(stock_io_logs):
            StockIOLog.objects.create(
                purchase=purchase,
                status=purchase.status,
                date=purchase.purchase_date,
                type=StockIOType.INPUT,
                organization_id=request.user.organization_id,
                entry_by=request.user,
                **item
            )

        return purchase


class PurchaseListSerializer(ModelSerializer):
    person_organization_supplier = PersonOrganizationSupplierSerializer(
        read_only=True, allow_null=True)
    store_point = StorePointSerializer()
    pending_amount = serializers.FloatField()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'requisition_date',
            'person_organization_supplier',
            'department',
            'amount',
            'discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'receiver',
            'remarks',
            'vouchar_no',
            'transport',
            'is_sales_return',
            # 'requisitions',
            'store_point',
            'pending_amount',
            'organization_department',
            'organization_wise_serial',
        )


class PurchaseSearchSerializer(PurchaseBasicSerializer):
    from core.serializers import PersonOrganizationEmployeeSearchSerializer
    person_organization_supplier = PersonOrganizationSupplierSerializer(
        read_only=True, allow_null=True)
    person_organization_receiver = PersonOrganizationEmployeeSearchSerializer()
    store_point = StorePointSerializer()
    department = DepartmentSerializer(read_only=True)
    pending_amount = serializers.FloatField()
    copied_from = PurchaseLiteSerializer()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchase_order_status',
            'purchase_date',
            'person_organization_supplier',
            'amount',
            'grand_total',
            'person_organization_receiver',
            'store_point',
            'department',
            'remarks',
            'vouchar_no',
            'copied_from',
            'pending_amount',
            'transaction_purchase',
            'purchase_payment',
            'organization_wise_serial',
        )


class PurchaseDetailsSerializer(PurchaseBasicSerializer):
    copied_from = PurchaseBasicSerializer(
        allow_null=True, default=None, many=False)
    requisitions = PurchaseBasicSerializer(
        allow_null=True, many=True)
    supplier = SupplierBasicSerializer(read_only=True, allow_null=True)
    person_organization_receiver = PersonOrganizationEmployeeSerializer(read_only=True)
    responsible_employee = PersonOrganizationEmployeeSerializer(read_only=True)
    stock_io_logs = StockIOLogDetailsWithUnitDetailsSerializer(read_only=True, many=True)
    department = DepartmentSerializer(read_only=True)
    person_organization_supplier = PersonOrganizationSupplierSerializer(
        read_only=True, allow_null=True)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_order_status',
            'purchase_date',
            'requisition_date',
            'supplier',
            'person_organization_supplier',
            'department',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'person_organization_receiver',
            'stock_io_logs',
            'remarks',
            'vouchar_no',
            'transport',
            'is_sales_return',
            'copied_from',
            'requisitions',
            'organization_wise_serial',
            'responsible_employee',
        )


class PurchaseListGetSerializer(ModelSerializer):
    store_point = StorePointSerializer(fields=('alias', 'name'))
    person_organization_supplier = PersonOrganizationLiteSerializer(
        read_only=True,
        allow_null=True,
        fields=('id', 'alias', 'company_name', 'first_name', 'last_name')
    )
    copied_from = PurchaseLiteSerializer()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'vouchar_no',
            'purchase_date',
            'person_organization_supplier',
            'store_point',
            'amount',
            'copied_from',
            'transport',
            'grand_total',
            'organization_department',
            'organization_wise_serial',
        )


class PurchaseOrderReportLiteSerializer(ModelSerializer):
    transaction_purchase = TransactionPurchaseLiteSerializer(many=True)
    class Meta:
        model = Purchase
        fields = (
            'id',
            'vouchar_no',
            'purchase_payment',
            'transaction_purchase'
        )


class PurchaseOrderReportSerializer(ModelSerializer):
    store_point = StorePointSerializer()
    supplier = SupplierBasicSerializer(read_only=True, allow_null=True)
    purchases = PurchaseOrderReportLiteSerializer(many=True)
    pending_amount = serializers.FloatField()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'vouchar_no',
            'purchase_date',
            'supplier',
            'store_point',
            'amount',
            'grand_total',
            'purchases',
            'pending_amount',
            'purchase_order_status',
        )


class StockAdjustmentBasicSerializer(ModelSerializer):
    stock_io_logs = StockIOLogSerializer(many=True, read_only=True)

    class Meta:
        model = StockAdjustment
        fields = (
            'id',
            'alias',
            'date',
            'store_point',
            'employee',
            'person_organization_employee',
            'patient',
            'service_consumed',
            'is_product_disbrustment',
            'patient_admission',
            'stock_io_logs',
            'status',
            'remarks',
        )


class StockAdjustmentSerializer(StockAdjustmentBasicSerializer):
    stock_io_logs = StockIOLogSerializer(many=True)

    class Meta:
        model = StockAdjustment
        fields = (
            'id',
            'alias',
            'date',
            'store_point',
            'employee',
            'patient',
            'person_organization_employee',
            'person_organization_patient',
            'is_product_disbrustment',
            'patient_admission',
            'service_consumed',
            'stock_io_logs',
            'disbursement_for',
            'remarks',
        )

    def create(self, validated_data):
        request = self.context.get("request")

        stock_io_logs = validated_data.pop('stock_io_logs', [])
        stock_io_log_list = request.data.get('stock_io_logs', [])
        stock_adjustment = StockAdjustment.objects.create(
            organization=request.user.organization,
            entry_by=request.user,
            **validated_data
        )

        for item in stock_io_logs:
            io_log = StockIOLog.objects.create(
                adjustment=stock_adjustment,
                status=stock_adjustment.status,
                date=stock_adjustment.date,
                patient=stock_adjustment.patient,
                organization=request.user.organization,
                entry_by=request.user,
                **item
            )
            if cause['cause']:
                StockIOLogDisbursementCause.objects.create(
                    stock_io_log=io_log,
                    disbursement_cause_id=cause['cause'],
                    number_of_usage=cause['usage'],
                    organization=request.user.organization,
                    entry_by=request.user,
                )

        return stock_adjustment


class StockAdjustmentDetailsSerializer(StockAdjustmentBasicSerializer):
    store_point = StorePointSerializer()
    stock_io_logs = StockIOLogDetailsSerializer(read_only=True, many=True)

class StockAdjustmentDetailsForDisburseSerializer(StockAdjustmentDetailsSerializer):
    stock_io_logs = StockIOLogDetailsWithDisbursementCauseSerializer(read_only=True, many=True)


class StockDisbursementListSerializer(ModelSerializer):
    from core.serializers import PersonOrganizationEmployeeSearchSerializer
    person_organization_employee = PersonOrganizationEmployeeSearchSerializer()
    store_point = StorePointModelSerializer.LiteList()

    class Meta:
        model = StockAdjustment
        fields = (
            'id',
            'alias',
            'date',
            'store_point',
            'person_organization_employee',
            'person_organization_patient',
            'is_product_disbrustment',
        )


class StockAdjustmentSearchSerializer(ModelSerializer):
    person_organization_employee = PersonOrganizationEmployeeLiteSerializer()
    store_point = StorePointSerializer()

    class Meta:
        model = StockAdjustment
        fields = (
            'id',
            'alias',
            'date',
            'store_point',
            'person_organization_employee',
            'person_organization_patient',
            'is_product_disbrustment',
            'patient_admission',
            'remarks',
        )


class SalesBasicSerializer(ModelSerializer):
    stock_io_logs = StockIOLogSerializer(many=True, read_only=True)
    store_point = StorePointSerializer(source='get_store_point_of_stock')
    salesman = PersonBasicSerializer()
    buyer = PersonBasicSerializer()
    vat_total = serializers.FloatField(read_only=True)
    vat_rate = serializers.FloatField(allow_null=True)

    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'sale_date',
            'store_point',
            'patient_admission',
            'prescription',
            'buyer',
            'amount',
            'discount',
            'salesman',
            'stock_io_logs',
            'remarks',
            'transport',
            'vat_rate',
            'vat_total',
            'copied_from',
            'transaction',
            'vouchar_no',
        )


class SalesServiceConsumedSerializer(ModelSerializer):
    stock_io_logs = StockIOLogDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'amount',
            'paid_amount',
            'stock_io_logs',
        )


class TaggedSalesSerializerForTransaction(ModelSerializer):

    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'organization_wise_serial',
        )


class SalesLedgerSerializer(ModelSerializer):
    grand_total = serializers.FloatField(default=0.00)
    stock_io_logs = StockIOLogDetailsSerializer(many=True, read_only=True)
    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'sale_date',
            'buyer',
            'amount',
            'paid_amount',
            'discount',
            'grand_total',
            'stock_io_logs',
        )


class SalesLedgerLiteSerializer(ModelSerializer):
    grand_total = serializers.FloatField(default=0.00)

    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'sale_date',
            'created_at',
            'amount',
            'grand_total',
        )


class SalesMinifiedSerializer(ModelSerializer):
    store_point = StorePointSerializer()

    class Meta:
        model = Sales
        fields = (
            'id',
            'alias',
            'sale_date',
            'store_point',
            'patient_admission',
            'prescription',
            'buyer',
            'amount',
            'discount',
            'vat_total',
            'round_discount',
            'paid_amount',
            'salesman',
            'remarks',
            'transport',
            'copied_from',
            'transaction',
            'vouchar_no',
        )


class PurchaseLedgerSerializer(ModelSerializer):
    '''
    A lite serializer for Purchase Model which will be used for Ledger
    '''
    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchase_date',
            'created_at',
            'amount',
            'grand_total',
        )



class PurchaseReturnSerializer(ModelSerializer):
    class Meta:
        model = PurchaseReturn
        fields = (
            'id',
            'sales',
            'status',
            'purchase',
            'organization',
            'entry_by',
        )


class PurchaseReturnLiteSerializer(ModelSerializer):
    class Meta:
        model = PurchaseReturn
        fields = (
            'id',
            'alias',
            'purchase'
        )


class StockReportSerializer(ModelSerializer):
    stock = StockSerializer()

    class Meta:
        model = StockIOLog
        fields = (
            'id',
            'alias',
            'stock',
            'quantity',
            'rate',
            'batch',
            'expire_date',
            'date',
            'type',
        )


class ProductLastUsageDateSerializer(Serializer):
    stock = serializers.IntegerField()
    last_usage = serializers.DateField()
    batch = serializers.CharField(default='N/A')


class StockProfitReportSerializer(ModelSerializer):
    stock = serializers.SerializerMethodField()
    total_quantity = serializers.FloatField()
    return_total_quantity = serializers.FloatField()
    received = serializers.FloatField()
    return_received = serializers.FloatField()
    discount = serializers.FloatField()
    return_discount = serializers.FloatField()
    vat = serializers.FloatField()
    return_vat = serializers.FloatField()
    calculated_price = serializers.FloatField()
    return_calculated_price = serializers.FloatField()
    calculated_price_organization_wise = serializers.FloatField()
    net_price = serializers.FloatField()
    return_net_price = serializers.FloatField()
    total_profit = serializers.SerializerMethodField()
    avg_purchase_rate = serializers.FloatField()

    # pylint: disable=old-style-class
    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'total_quantity',
            'return_total_quantity',
            'received',
            'return_received',
            'discount',
            'return_discount',
            'vat',
            'return_vat',
            'calculated_price',
            'return_calculated_price',
            'calculated_price_organization_wise',
            'net_price',
            'return_net_price',
            'total_profit',
            'avg_purchase_rate',
        )

    def get_total_profit(self, _obj):
        return _obj['total_profit'] if _obj['return_total_quantity'] \
            else _obj['sales_profit']

    def get_stock(self, obj):
        return construct_stock_object_from_dictionary(obj)


class StockProfitReportSummarySerializer(ModelSerializer):
    store_point = serializers.SerializerMethodField()
    total_quantity = serializers.FloatField()
    return_total_quantity = serializers.FloatField()
    received = serializers.FloatField()
    return_received = serializers.FloatField()
    discount = serializers.FloatField()
    return_discount = serializers.FloatField()
    vat = serializers.FloatField()
    return_vat = serializers.FloatField()
    net_price = serializers.FloatField()
    return_net_price = serializers.FloatField()
    total_profit = serializers.SerializerMethodField()

    # pylint: disable=old-style-class
    class Meta:
        model = StockIOLog
        fields = (
            'store_point',
            'total_quantity',
            'return_total_quantity',
            'received',
            'return_received',
            'discount',
            'return_discount',
            'vat',
            'return_vat',
            'net_price',
            'return_net_price',
            'total_profit',
        )

    def get_store_point(self, obj):
        return obj['stock__store_point__name']

    def get_total_profit(self, _obj):
        return _obj['total_profit'] if _obj['return_total_quantity'] \
            else _obj['sales_profit']


class EmployeeStorepointAccessBasicSerializer(ModelSerializer):

    class Meta:
        model = EmployeeStorepointAccess
        fields = (
            'id',
            'alias',
            'employee',
            'person_organization',
            'store_point',
            'access_status',
        )


class EmployeeStorepointAccessSerializer(EmployeeStorepointAccessBasicSerializer):
    # employee = EmployeeSerializer(read_only=True)
    store_point = StorePointSerializer(read_only=True)


class EmployeeAccountAccessSerializer(ModelSerializer):
    from core.serializers import EmployeeSerializer

    # employee = EmployeeSerializer()
    class Meta:
        model = EmployeeAccountAccess
        fields = (
            'id',
            'alias',
            'employee',
            'access_status',
        )


class EmployeeAccountAccessBasicSerializer(ModelSerializer):

    class Meta:
        model = EmployeeAccountAccess
        fields = (
            'id',
            'alias',
            'employee',
            'account',
            'access_status',
        )


class PurchaseOrderRestItemSerializer(Serializer):
    """
    Serializer for getting total balance till a specific date.
    """
    stock_io_logs__stock__product = serializers.IntegerField()
    ordered = serializers.FloatField()
    received = serializers.FloatField()
    rest_item = serializers.FloatField()


class PurchaseRequisitionSerializer(ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = (
            'id',
            'requisition',
            'purchase',
            'organization',
            'entry_by',
        )


class SalesReturnSerializer(ModelSerializer):
    class Meta:
        model = SalesReturn
        fields = (
            'id',
            'purchase',
            'sales',
            'organization',
            'entry_by',
        )


class ProductOpeningStockSerializer(ModelSerializer):
    product = ProductWithoutUnitSerializer()
    store_point = StorePointSerializer()
    opening_stock = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'product',
            'store_point',
            'opening_stock',
            'purchase_rate',
        )

    def get_opening_stock(self, obj):
        return int(obj.sum)


class StockDetailsReportSerializer(ModelSerializer):
    product = serializers.SerializerMethodField()
    store_point = serializers.SerializerMethodField()
    sales_sum = serializers.FloatField()
    sales_price = serializers.FloatField()
    purchase_sum = serializers.FloatField()
    purchase_price = serializers.FloatField()
    transfer_in = serializers.FloatField()
    transfer_out = serializers.FloatField()
    disbursement = serializers.FloatField()
    adjustment_in = serializers.FloatField()
    adjustment_out = serializers.FloatField()
    opening_stock = serializers.FloatField()

    class Meta:
        model = Stock
        fields = (
            'product',
            'store_point',
            'purchase_rate',
            'sales_sum',
            'sales_price',
            'purchase_sum',
            'purchase_price',
            'transfer_in',
            'transfer_out',
            'disbursement',
            'adjustment_in',
            'adjustment_out',
            'opening_stock',
        )

    def get_product(self, obj):
        return construct_product_object_from_dictionary(obj)

    def get_store_point(self, obj):
        return construct_store_point_object_from_dictionary(obj)


class InventorySummarySerializer(Serializer):
    store_point = serializers.SerializerMethodField()
    date = serializers.DateField()
    quantity = serializers.FloatField()

    def get_store_point(self, obj):
        return obj['stock__store_point__name']


class ProductMergeSerializer(Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            status=Status.ACTIVE
        )
    )
    clone_product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            status=Status.ACTIVE
        )
    )

    def create(self, validated_data):
        pass


class StoreWiseSalesGraphSerializer(ModelSerializer):
    value = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    # pylint: disable=old-style-class
    class Meta:
        model = Sales
        fields = (
            'store',
            'date',
            'value',
        )

    def get_store(self, obj):
        return obj['store_point__name']

    def get_date(self, obj):
        return obj['sale_date']

    def get_value(self, obj):
        return obj['value']


class CompanyWiseSalesGraphSerializer(ModelSerializer):
    name = serializers.SerializerMethodField()
    y = serializers.SerializerMethodField()

    # pylint: disable=old-style-class
    class Meta:
        model = Sales
        fields = (
            'name',
            'y',
        )

    def get_name(self, obj):
        return obj['stock_io_logs__stock__product__manufacturing_company__name']

    def get_y(self, obj):
        return obj['value']


class DistributorOrderStateSerializer(ModelSerializer):
    # pylint: disable=old-style-class
    class Meta:
        model = Stock
        fields = (
            'id',
            'product_full_name',
            'avg_daily_order_quantity',
            'avg_daily_order_count',
            'avg_daily_discount'
        )

