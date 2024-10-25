import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.models import OrganizationSetting
from core.tests import OrganizationFactory

from common.enums import (
    Status,
    PublishStatus,
    DiscardType,
)

from ..enums import (
    StockIOType,
    GlobalProductCategory)
from ..models import (
    Product,
    ProductManufacturingCompany,
    ProductForm,
    ProductGroup,
    ProductSubgroup,
    ProductGeneric,
    Unit,
    ProductCategory,
    StorePoint,
    Stock,
    StockAdjustment,
    StockIOLog,
    OrganizationWiseDiscardedProduct,
)

fake = Faker()

def get_nameslugbased_data(organization, _type, extra=None):
    '''
    generating data for creating name slug based object
    '''
    data = {
        'name': fake.first_name(),
        'status': Status.ACTIVE,
        'organization': organization,
        'is_global': _type
    }

    if extra is not None:
        data.update(extra)

    return data

def create_random_product(organization=None, global_product_type=None, _type=None):
    '''
    create a random product
    '''

    # if type is not provided then 50 - 50 chance of creating private or global product
    if _type is None:
        _type = PublishStatus.PRIVATE
        if bool(random.getrandbits(1)):
            _type = PublishStatus.INITIALLY_GLOBAL

    pm_company = ProductManufacturingCompany.objects.create(
        **get_nameslugbased_data(organization, _type))

    pm_company.save()

    form = ProductForm.objects.create(
        **get_nameslugbased_data(organization, _type))
    form.save()

    group = ProductGroup.objects.create(
        **get_nameslugbased_data(organization, _type))
    group.save()

    subgroup = ProductSubgroup.objects.create(
        **get_nameslugbased_data(organization, _type, {'product_group': group})
    )
    subgroup.save()

    generic = ProductGeneric.objects.create(
        **get_nameslugbased_data(organization, _type)
    )

    primary_unit = Unit.objects.create(
        **get_nameslugbased_data(organization, _type)
    )
    primary_unit.save()

    sec_unit = Unit.objects.create(
        **get_nameslugbased_data(organization, _type)
    )
    sec_unit.save()

    category = ProductCategory.objects.create(
        **get_nameslugbased_data(organization, _type)
    )
    category.save()
    sales_price = random.randint(1, 12)

    product_data = {
        'name': fake.first_name(),
        'organization': organization,
        'trading_price': sales_price,
        'purchase_price': sales_price - (sales_price*.01),
        'manufacturing_company': pm_company,
        'form': form,
        'subgroup': subgroup,
        'generic': generic,
        'primary_unit': primary_unit,
        'secondary_unit': sec_unit,
        'conversion_factor': random.randint(1, 10),
        'category': category,
        'is_global': _type,

    }

    # global_category is only important if and only if product is global
    if _type == PublishStatus.INITIALLY_GLOBAL:
        product_data.update({'global_category': global_product_type})

    product = Product.objects.create(**product_data)
    product.save()

    return product

def create_stock_adjustment(product, storepoint, quantity, _type, entry_by,):
    '''
    this method create a stock adjustment entry for given data
    '''

    stock = Stock.objects.get(
        product=product,
        store_point=storepoint,
    )

    adjustment = StockAdjustment.objects.create(
        date=fake.date(),
        store_point=storepoint,
        is_product_disbrustment=False,
        adjustment_type=_type,
        organization=entry_by.organization,
        entry_by=entry_by
    )
    adjustment.save()

    io_log = StockIOLog.objects.create(
        stock=stock,
        quantity=quantity,
        rate=product.purchase_price,
        type=_type,
        adjustment=adjustment,
        primary_unit=product.primary_unit,
        organization=entry_by.organization,
    )
    io_log.save()

def get_product_type(product):
    '''
    this method return product type
    '''

    if product.is_global == PublishStatus.PRIVATE:
        return "private"
    return "global"

def enable_global_setup(organization, global_product_type):
    '''
    this method enable global product population for an organization
    '''
    organization.show_global_product = True
    organization.save()

    settings = OrganizationSetting.objects.get(
        organization=organization
    )
    settings.global_product_category = global_product_type
    settings.save()

def create_stock_io_adjustment(product, storepoint, admin_user):
    '''
    create a stock adjustment entry for given data
    '''
    number_of_io_entry = random.randint(2, 5)

    stock_count = 0

    for _index in range(1, number_of_io_entry + 1):

        product_in = random.randint(2, 100)
        product_out = product_in - random.randint(1, product_in-1)

        # want to create a 50 50 chance of stock geting cleared
        if bool(random.getrandbits(1)):
            product_in = product_out

        create_stock_adjustment(
            product, storepoint, product_in, StockIOType.INPUT, admin_user)
        create_stock_adjustment(
            product, storepoint, product_out, StockIOType.OUT, admin_user)

        stock_count = stock_count + (product_in - product_out)

    return number_of_io_entry, stock_count

def create_storepoint(organization):

    storepoint = StorePoint.objects.create(
        name=fake.first_name(),
        organization=organization,
        phone="017112233665",
        address=fake.address(),
        populate_global_product=True
    )
    storepoint.save()
    return storepoint

class ProductMergeAPITest(OmisTestCase):
    url = reverse('product-merge')

    def setUp(self):

        super(ProductMergeAPITest, self).setUp()
        self.organization = self.admin_user.organization

        # randmonly selecting GPA or GPB
        self.global_product_type = GlobalProductCategory.GPA if random.randint(
            0, 1) == 0 else GlobalProductCategory.GPB
        # making sure organization works with global product
        enable_global_setup(self.organization, self.global_product_type)

        # creating another organization
        self.another_organization = OrganizationFactory()
        enable_global_setup(self.another_organization,
                            self.global_product_type)

        self.storepoint_1 = create_storepoint(self.organization)
        self.storepoint_2 = create_storepoint(self.organization)
        self.storepoint_3 = create_storepoint(self.another_organization)

    def test_product_merge(self):

        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # creating a random number to run test
        number_of_test = random.randint(20, 50)

        for index in range(0, number_of_test):

            product_1 = create_random_product(
                self.organization, self.global_product_type)
            product_2 = create_random_product(
                self.organization, self.global_product_type)

            num_of_io_product_1, product_1_stock_count = create_stock_io_adjustment(
                product_1, self.storepoint_1, self.admin_user
            )

            num_of_io_product_2, product_2_stock_count = create_stock_io_adjustment(
                product_2, self.storepoint_1, self.admin_user
            )

            data = {
                'clone_product': product_1.id,
                'product': product_2.id
            }

            self.client.post(self.url, data=json.dumps(
                dict(data)), content_type='application/json')

            final_stock = Stock.objects.get(
                product=product_2, store_point=self.storepoint_1)

            self.assertEqual(product_1_stock_count +
                             product_2_stock_count, final_stock.stock)

            product_1_after_merge = Product.objects.filter(
                pk=product_1.id, status=Status.ACTIVE)
            product_2_after_merge = Product.objects.filter(
                pk=product_2.id, status=Status.ACTIVE)

            # if product_1 is private it should not exist and neither its stock
            if product_1.is_global == PublishStatus.PRIVATE:
                stock_of_product_1 = Stock.objects.filter(
                    product=product_1,
                    status=Status.ACTIVE,
                    organization=self.organization
                )

                # stock of product 1  no more exists
                self.assertEqual(stock_of_product_1.count(), 0)
                # product 1 no more exists
                self.assertEqual(product_1_after_merge.count(), 0)

            else:
                stock_of_product_1 = Stock.objects.filter(
                    product=product_1,
                    status=Status.ACTIVE,
                    organization=self.another_organization
                )
                # as product 1 is global product its accible on another organization
                self.assertEqual(stock_of_product_1.count(), 1)

            # as product 2 was primary product it exist on self.organization
            self.assertEqual(product_2_after_merge.count(), 1)

            # stock io of of product 1
            product_1_stock_io_after_merge = StockIOLog.objects.filter(
                stock__product=product_1,
                organization=self.organization
            )

            # stock io of of product 2
            product_2_stock_io_after_merge = StockIOLog.objects.filter(
                stock__product=product_2,
                organization=self.organization
            )

            # no stock io with product 1 should exists
            self.assertEqual(product_1_stock_io_after_merge.count(), 0)

            # all stock io of product 1 shall converted as product 1 hence
            self.assertEqual(
                product_2_stock_io_after_merge.count(),
                2*(num_of_io_product_1 + num_of_io_product_2)
            )
            # Compare product full name with stock product full_name
            self.assertEqual(
                product_2.full_name.lower(),
                product_2_stock_io_after_merge.first().stock.product_full_name
            )
            # checking if discarded entry was successfull
            discarded_entry = OrganizationWiseDiscardedProduct.objects.filter(
                product=product_2,
                parent=product_1,
                entry_type=DiscardType.MERGE,
                organization=self.organization,
                status=Status.ACTIVE
            )
            self.assertEqual(discarded_entry.count(), 1)

            # prining activity
            print("test {}: after {} entries, {} <---  {} succesfull".format(
                str(index+1).ljust(3, " "),
                str(2*(num_of_io_product_1)).ljust(3, " "),
                get_product_type(product_2).ljust(8, " "),
                get_product_type(product_1).ljust(8, " ")
            ))
