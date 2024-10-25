# from __future__ import division
# from future.builtins import round
# from common.tasks import send_sms
# from common.helpers import generate_phone_no_for_sending_sms, get_key_by_enum_value
# from account.enums import OmisServices

# from .enums import Months


# def post_save_payment_response(sender, instance, created, **kwargs):
#     if created and instance.data['status'] == "VALID":
#         organization = instance.ipn.payment_request.organization
#         amount = instance.data['amount']
#         purpose = get_key_by_enum_value(OmisServices, instance.ipn.payment_request.payment_purpose)
#         month = get_key_by_enum_value(Months, instance.ipn.payment_request.payment_month)
#         sms_to = generate_phone_no_for_sending_sms(organization.primary_mobile)
#         sms_text = "Thank you for your payment of BDT {} for the month of {} for {}.".format(
#             amount,
#             month,
#             purpose
#         )
#         # Sending sms to client
#         send_sms.delay(
#             sms_to,
#             sms_text,
#             organization.id
#         )
