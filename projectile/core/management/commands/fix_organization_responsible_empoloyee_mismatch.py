import datetime
import logging

from django.core.management import BaseCommand
from tqdm import tqdm

from common.helpers import query_yes_no, populate_es_index
from core.models import Organization, PersonOrganization
from ecommerce.models import OrderInvoiceGroup
from common.enums import Status
from pharmacy.enums import OrderTrackingStatus

logger = logging.getLogger('Global Log')

class Command(BaseCommand):
    help = 'Fixes Organization Responsible Employee Mismatch'

    def handle(self, *args, **kwargs):
        organizations = Organization.objects.filter().values('id', 'primary_responsible_person').exclude(
            status=Status.INACTIVE)
        invoice_groups = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            responsible_employee__isnull=False,
        ).select_related('order_by_organization').values(
            'delivery_date',
            'responsible_employee',
            'order_by_organization'
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED
            ]
        ).order_by('-delivery_date').distinct('delivery_date', 'order_by_organization')

        invoices_group_by_organization = {}
        for invoice_group in invoice_groups:
            organization_id = invoice_group['order_by_organization']
            if organization_id not in invoices_group_by_organization:
                invoices_group_by_organization[organization_id] = []
            invoices_group_by_organization[organization_id].append(invoice_group)

        invoices_minimum_three_deliveries = {}
        for organization in invoices_group_by_organization:
            if len(invoices_group_by_organization[organization]) >= 3:
                invoices_minimum_three_deliveries[organization] = invoices_group_by_organization[organization]
            else:
                invoices_minimum_three_deliveries[organization] = None

        invoices_res_emp_by_org = {}
        for organization in invoices_minimum_three_deliveries:
            invoices_res_emp_by_org[organization] = None
            if invoices_minimum_three_deliveries[organization] is not None:
                employees = []
                for invoice_group in invoices_minimum_three_deliveries[organization]:
                    employees.append(invoice_group['responsible_employee'])
                responsible_employee_id = []
                if len(employees) > 0:
                    # Check if the employee is responsible for 3 consecutive deliveries
                    for index in range(len(employees) - 2):
                        if employees[index] == employees[index + 1] and employees[index + 1] == employees[index + 2]:
                            responsible_employee_id.append(employees[index])
                if len(responsible_employee_id) > 0:
                    invoices_res_emp_by_org[organization] = responsible_employee_id[0]
                employees.clear()
                responsible_employee_id.clear()

        obj_to_be_updated = []
        organization_ids = []
        question = f"Do you want to update the primary responsible employee of the organizations based on invoices " \
                   f"responsible person? "
        if not query_yes_no(question, "no"):
            return
        for org in tqdm(organizations):
            # If invoices_res_emp_by_org dict has the current organization in it, that means the organization has
            # three or more deliveries, then we will check primary responsible person mismatch
            if org["id"] in invoices_res_emp_by_org.keys():

                # Use case for below IF condition: suppose 5 deliveries are done
                # by 5 different employee, then we will not update the primary responsible person
                if invoices_res_emp_by_org[org["id"]] is not None:
                    if invoices_res_emp_by_org[org["id"]] != org["primary_responsible_person"]:
                        obj_to_be_updated.append(
                            Organization(
                                id=org["id"],
                                primary_responsible_person=PersonOrganization.objects.get(
                                    pk=invoices_res_emp_by_org[org["id"]])

                            )
                        )
                        organization_ids.append(org["id"])
            else:
                # Now, If we didn't find any possible responsible person for the organization
                # then we will make those organizations primary responsible person as None
                # if org["primary_responsible_person"] is not None:
                #     obj_to_be_updated.append(
                #         Organization(
                #             id=org["id"],
                #             primary_responsible_person=None
                #         )
                #     )

                # reason we are not updating the primary responsible person to None is because
                # sometime, the organization has less than 3 delivery, and in that case, we don't want to update
                pass

        Organization.objects.bulk_update(
            obj_to_be_updated,
            ['primary_responsible_person'],
            batch_size=100
        )

        populate_es_index(
            'core.models.Organization',
            {'id__in': organization_ids},
        )

        logger.info("Done!!!")
