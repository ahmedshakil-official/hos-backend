from django.urls import reverse

from common.utils import inactive_instance
from common.test_case import OmisTestCase
from pharmacy.tests import UnitFactory, ProductFactory


class UnitSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.unit-search')

    # def setUp(self):
    #     super(UnitSearchAPITest, self).setUp()

    def test_unit_search_list(self):
        # first create some unit
        data1 = UnitFactory(name="unit1")
        data2 = UnitFactory(name="unit2")

        product1 = ProductFactory(
            name="product1",
            primary_unit=data1,
            secondary_unit=data1
        )

        # search data
        search_data = {
            'keyword': 'uni',
            # 'product': 'testproduct1'
        }

        search_data2 = {
            'keyword': 'zzz',
            # 'product': 'testproduct2'
        }

        search_data_wuth_prodcut = {
            'keyword': 'uni',
            'product': product1.alias
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, search_data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, search_data)
        # self.assertPermissionDenied(request)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # ===============================================
        #  Check for admin user of the same organization
        # ===============================================
        data1.organization = self.admin_user.organization
        data1.save()
        data2.organization = self.admin_user.organization
        data2.save()

        product1.organization = self.admin_user.organization
        product1.save()

        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # Check productwise unit
        request = self.client.get(self.url, search_data_wuth_prodcut)
        self.assertSuccess(request)

        # Compare data
        self.assertEqual(request.data['count'], 1)

        inactive_instance(data1)

        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 1)

        # check with other data
        request = self.client.get(self.url, search_data2)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
