import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import logging
from commons import config, NotificationLogger
from commons.utils import retry

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class Email:
    def __init__(self):
        self.smtp_host = config.SMTP_SERVER_HOST
        self.smtp_port = config.SMTP_SERVER_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_pwd = config.SMTP_PASSWORD
        self.email_from = config.SMTP_EMAIL_FROM

    @retry(max_retries=3, delay=1, backoff=2)
    def mail(self, body, subject, to, cc="", bcc="", replyto=""):

        try:
            if to is None:
                msg = "Email Receipient is not valid"
                return msg
            
            if type(to) is type([]) : to = ", ".join(to)
            if type(cc) is type([]) : cc = ", ".join(cc)
            if type(bcc) is type([]) : bcc = ", ".join(bcc)

            recipient = to.split(',') + cc.split(',') + bcc.split(',')

            message = MIMEText(body, 'html')
            message['From'] = self.email_from
            message['To'] = to
            message['Cc'] = cc
            message['Bcc'] = bcc
            message['Subject'] = subject

            msg_full = message.as_string()

            server = smtplib.SMTP( self.smtp_host + ':' + str(self.smtp_port))
            server.starttls()
            server.login(self.smtp_user, self.smtp_pwd)
            server.sendmail(self.email_from , recipient, msg_full)

            server.quit()
            return f"Mail Sent to {to}"
        except Exception as e:
            logger.error(f"Exception in send email : {str(e)}")
            raise e