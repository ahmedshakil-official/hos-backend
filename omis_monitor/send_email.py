# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config


def send_email(text, email_logger):
    email_logger.debug('Preparing emails')
    try:
        # Create a html message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'OMIS Service(s) are down'
        msg['From'] = config.EMAIL['FROM']

        txt = MIMEText(text[0], 'plain')
        htm = MIMEText(text[1], 'html')
        msg.attach(txt)
        msg.attach(htm)

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        email_logger.debug('Connecting to SMTP')
        connection = smtplib.SMTP(config.EMAIL['HOST'], config.EMAIL['PORT'])
        email_logger.debug('Logging in to SMTP')
        connection.login(config.EMAIL['USERNAME'], config.EMAIL['PASSWORD'])

        for to_address in config.EMAIL['TO']:
            msg['To'] = to_address
            email_logger.debug('Sending email')
            connection.sendmail(config.EMAIL['FROM'], [to_address, ], msg.as_string())
            connection.quit()
            email_logger.debug('Email sent')
    except Exception:
        email_logger.error('Can not send email')
