import json

from procurement.serializers.procure import ProcureModelSerializer
from procurement.serializers.procure_issue_log import ProcureIssueLogModelSerializer
from procurement.serializers.procure_status import ProcureStatusModelSerializer


def update_procure_organization_with_user_organization(procure, organization_id):
    """
    Update the organization ID for a procure instance with the provided organization ID.

    Args:
    - procure: The Procure instance to be updated.
    - organization_id: The ID of the organization to set.

    Returns:
    The updated organization associated with the procure instance.
    """
    procure.organization_id = organization_id
    procure.save()
    return procure.organization


def check_procure_list_fields(self, request):
    """
    Check if specific fields are present in the JSON response received.

    Args:
    - self: Reference to the class instance.
    - request: The HTTP request object containing the JSON response.

    Notes:
    This function assumes that the 'request' object contains a JSON response
    structured in a particular format.
    """

    # Instantiate your serializer
    serializer = ProcureModelSerializer.List()

    # Fields previously defined and expected in the JSON response

    previously_defined_fields = [
        "id",
        "alias",
        "date",
        "supplier",
        "contractor",
        "employee",
        "requisition",
        "sub_total",
        "discount",
        "operation_start",
        "operation_end",
        "remarks",
        "invoices",
        "estimated_collection_time",
        "current_status",
        "medium",
        "credit_amount",
        "paid_amount",
        "is_credit_purchase",
        "credit_payment_term",
        "credit_payment_term_date",
        "credit_cost_percentage",
        "credit_cost_amount",
        "open_credit_balance"
    ]
    # Load JSON string to a Python dictionary
    data = request.json()["results"][0]

    # Check if all fields from the list are present in the JSON response
    all_present = all(field in data for field in previously_defined_fields)

    self.assertTrue(
        all_present,
        msg="Some fields are missing in serializer which was previously defined!"
    )

    # Check if every field defined in the serializer is available in the response
    current_serializer_fields = (serializer.fields.keys())
    all_present = all(field in data for field in current_serializer_fields)
    self.assertTrue(
        all_present,
        msg="Some fields are missing in response which are declared in serializer!"
    )


def check_procure_status_list_fields(self, request):
    """
    Check if specific fields are present in the JSON response received.

    Args:
    - self: Reference to the class instance.
    - request: The HTTP request object containing the JSON response.

    Notes:
    This function assumes that the 'request' object contains a JSON response
    structured in a particular format.
    """

    # Instantiate your serializer
    serializer = ProcureStatusModelSerializer.List()

    # Fields previously defined and expected in the JSON response

    previously_defined_fields = [
        "id",
        "alias",
        'current_status',
        'procure',
        'remarks',
    ]
    # Load JSON string to a Python dictionary
    data = request.json()["results"][0]

    # Check if all fields from the list are present in the JSON response
    all_present = all(field in data for field in previously_defined_fields)

    self.assertTrue(
        all_present,
        msg="Some fields are missing in serializer which was previously defined!"
    )

    # Check if every field defined in the serializer is available in the response
    current_serializer_fields = (serializer.fields.keys())
    all_present = all(field in data for field in current_serializer_fields)
    self.assertTrue(
        all_present,
        msg="Some fields are missing in response which are declared in serializer!"
    )

def check_procure_issue_log_list_fields(self, request):
    """
    Check if specific fields are present in the JSON response received.

    Args:
    - self: Reference to the class instance.
    - request: The HTTP request object containing the JSON response.

    Notes:
    This function assumes that the 'request' object contains a JSON response
    structured in a particular format.
    """

    # Instantiate your serializer
    serializer = ProcureIssueLogModelSerializer.List()

    # Fields previously defined and expected in the JSON response

    previously_defined_fields = [
        "id",
        "alias",
        "date",
        "supplier",
        "employee",
        "stock",
        "prediction_item",
        "type",
        "remarks",
    ]
    # Load JSON string to a Python dictionary
    data = request.json()["results"][0]

    # Check if all fields from the list are present in the JSON response
    all_present = all(field in data for field in previously_defined_fields)

    self.assertTrue(
        all_present,
        msg="Some fields are missing in serializer which was previously defined!"
    )

    # Check if every field defined in the serializer is available in the response
    current_serializer_fields = (serializer.fields.keys())
    all_present = all(field in data for field in current_serializer_fields)
    self.assertTrue(
        all_present,
        msg="Some fields are missing in response which are declared in serializer!"
    )
