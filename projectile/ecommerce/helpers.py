import os
from common.tasks import send_message_to_slack_or_mattermost_channel_lazy


def send_delayed_delivery_message_to_mm(message):
    send_message_to_slack_or_mattermost_channel_lazy.delay(
        os.environ.get("DELIVERY_DELAYED_LOG_CHANNEL_ID", ""),
        message
    )