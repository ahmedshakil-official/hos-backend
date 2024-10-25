import os, logging
import asyncio
import pymsteams
logger = logging.getLogger(__name__)


def send_message_to_teams_channel(web_hook_url="", message=""):
    """[summary]
    will send text message to teams channel
    Keyword Arguments:
        web_hook_url {str} -- [Web hook url for MS Teams in which text will be sent] (default: {""})
        message {str} -- [text message] (default: {""})
    """
    logger.info(message)
    try:
        teams_message = pymsteams.connectorcard(web_hook_url)
        teams_message.text(message)
        teams_message.send()
    except Exception as exception:
        logger.error(f"Error sending message to slack/mattermost/Teams. Exception: {str(exception)}")
