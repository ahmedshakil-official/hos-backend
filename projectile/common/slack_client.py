import os
import logging
import slack
import nest_asyncio
nest_asyncio.apply()

logger = logging.getLogger(__name__)

client = slack.WebClient(token=os.environ.get('SLACK_API_TOKEN', ''))


def send_file_to_slack_channel(channel="", path="", title="", description=""):
    """[summary]
    will send / upload file to a specific slack channel
    Keyword Arguments:
        channel {str} -- [channel id in which file will be uploaded] (default: {""})
        path {str} -- [path of the file] (default: {""})
        title {str} -- [title of the file] (default: {""})
        description {str} -- [description of the file] (default: {""})

    Returns:
        [str] -- [file download url]
    """

    if not (client and channel):
        logger.error("Missing slack api token or channel id")
        return

    file_name = os.path.basename(path)
    data = {
        'channels': channel,
        'filename': file_name,
        'title': title,
        'initial_comment': description
    }

    with open(path, 'rb') as file_content:
        response = client.api_call("files.upload", files={
            'file': file_content,
        }, data=data)
    return response['file']['url_private_download']


def send_message_to_slack_channel(channel="", message=""):
    """[summary]
    will send text message to slack channel
    Keyword Arguments:
        channel {str} -- [channel id in which text will be sent] (default: {""})
        message {str} -- [text message] (default: {""})
    """
    logger.info(message)
    if not (client and channel):
        logger.error("Missing slack api token or channel id")
        return

    response = client.chat_postMessage(
        channel=channel,
        text=message,
    )
