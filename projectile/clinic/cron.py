import logging

from django.utils import timezone
from django.db.models import Q, F

from common.tasks import send_sms
from core.models import OrganizationSetting

from .models import AppointmentSchedule


logger = logging.getLogger(__name__)


def send_sms_to_treatment_sessions():
    logger.info("Starting bulk SMS sending to Appointment Scheduled patients at {}.".format(
        timezone.now()))

    # Find all the appointments of today which are organization sms and treatment_session sms is on and SMS not sent
    schedules_today = AppointmentSchedule.objects.filter(
        Q(last_cron_update__lt=(timezone.now() -
                                timezone.timedelta(days=1))) | Q(last_cron_update=None),
        days=timezone.now().weekday(),
        treatment_session__start_time__gte=(
            timezone.now().time() + F('treatment_session__send_sms_before')),
        treatment_session__start_time__lte=(timezone.now().time() +
                                            F('treatment_session__send_sms_before') +
                                            timezone.timedelta(minutes=30)),
        treatment_session__send_sms=True,
        organization__id__in=OrganizationSetting.objects.filter(
            appointment_bulk_sms=True
        ).values_list('organization__id', flat=True)
    )

    logger.info("Filtered Appointment Schedule List successfully from the system.")
    sent_sms = 0

    # send sms to all the filtered appointment schedules
    for schedule in schedules_today:
        # prepare SMS for sending
        sms_body = 'You have an appointment today at {} in {}'.format(
            schedule.treatment_session.start_time,
            schedule.organization.name
        )
        # send sms
        send_sms.delay(schedule.person.phone, sms_body, schedule.organization.id)
        # update the instance
        schedule.last_cron_update = timezone.now()
        schedule.save()
        # increase sms count
        sent_sms += 1

    logger.info("Successfully Sent {} SMS(s) at {}.".format(sent_sms, timezone.now()))
