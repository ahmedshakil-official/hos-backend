import json
import requests

# import configuration
import config


def send_sms_client(sms_to, sms_text):
    url = 'https://api.infobip.com/sms/1/text/single/'
    api_key = config.SMS['INFOBIP_API_KEY']
    headers = {}
    headers["Authorization"] = "App %s" % api_key
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = {
        "to": sms_to,
        "text": sms_text
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.content


def send_sms(text, sms_logger):
    # configuration part
    sms_logger.debug('Connecting to SMS gateway')
    try:
        sms_logger.debug('Sending SMS')
        # sending sms to the list
        for sms_to in config.SMS['TO']:
            response = send_sms_client(sms_to, text)
            sms_logger.info(response)
        sms_logger.debug('SMS sent')

    except Exception:
        sms_logger.error('SMS gateway connection failed')
