from django.db.models import Q
from django.urls import reverse
from common.test_case import OmisTestCase
from core.enums import PersonGroupType
from core.tests import EmployeeFactory, SupplierFactory
from core.models import PersonOrganization
from faker import Faker


class PersonOrganizationEmployeeListSearchAPITest(OmisTestCase):
    url = reverse('person-organization-employee-supplier-search')
    fake = Faker()

    def test_person_oganization_employee_list_search_get(self):
        previous_count = PersonOrganization.objects.filter(
            Q(person_group=PersonGroupType.EMPLOYEE) | Q(person_group=PersonGroupType.SUPPLIER)
        ).count()
        employee = EmployeeFactory(
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name(),
            organization=self.admin_user.organization
        )
        supplier = SupplierFactory(
            company_name=employee.first_name, organization=self.admin_user.organization)

        # search data
        data1 = {
            'keyword': 'qwe',
        }

        data2 = {
            'keyword': str(employee.first_name),
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # test with keyword that return none
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check is it return 0 data
        self.assertEqual(request.data['count'], 0)

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # Check data in the database
        query_from_database = PersonOrganization.objects.filter(
            (Q(person_group=PersonGroupType.EMPLOYEE) | Q(person_group=PersonGroupType.SUPPLIER)),
        ).count() - previous_count

        self.assertEqual(request.data['count'], query_from_database)

        self.assertEqual(
            request.data['results'][1]['first_name'],
            employee.first_name)
        self.assertEqual(
            request.data['results'][1]['last_name'],
            employee.last_name)

        # logout
        self.client.logout()
