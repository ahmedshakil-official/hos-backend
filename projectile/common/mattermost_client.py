import os, logging
import mattermost
logger = logging.getLogger(__name__)

bot_token = os.environ.get('MATTERMOST_BOT_TOKEN', '')
mm_api = os.environ.get('MATTERMOST_API_URL', '')

client = mattermost.MMApi(mm_api)
client.login(bearer=bot_token)


def send_message_to_mattermost_channel(channel_id="", message=""):
    """[summary]
    will send text message to slack channel
    Keyword Arguments:
        channel {str} -- [channel id in which text will be sent] (default: {""})
        message {str} -- [text message] (default: {""})
    """
    logger.info(message)
    try:
        if not (client and channel_id):
            logger.error("Missing Mattermost api token or channel id")
            return

        client.create_post(channel_id, message)
    except:
        logger.error("Error sending message to slack/mattermost.")
