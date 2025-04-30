import datetime
import logging
from commons import NotificationLogger
import firebase_admin
from firebase_admin import credentials, messaging
from commons.utils import retry

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class Push:
    def __init__(self):
        self.firebase_cred = credentials.Certificate("service-account.json")
        self.firebase_app = firebase_admin.initialize_app(self.firebase_cred)

    @retry(max_retries=3, delay=1, backoff=2)
    def send_push(self, notification_details):
        try:
            if notification_details.get('token') is None:
                msg = "Token is not valid"
                return msg
            if notification_details.get('PushTitle') is None or notification_details.get('PushContent') is None:
                msg = "Invalid Push Configuration"
                return msg
            
            deviceToken       = notification_details.get('token')
            MsgTitle    = notification_details.get('PushTitle')
            MsgBody     = notification_details.get('PushContent')
            ActionUrl   = notification_details.get('ActionLink')

            _aps = messaging.Aps(
                sound = "default",
                badge = 1,
                mutable_content     = True,
                content_available   = True
            )
            _apsPayload = messaging.APNSPayload(aps=_aps)

            _apns = messaging.APNSConfig(payload=_apsPayload, headers={
                "apns-push-type": "background",
                "apns-priority": "5",
                "apns-topic": "io.flutter.plugins.firebase.messaging",
            })

            _android = messaging.AndroidConfig(
                priority = 'high'
            )
            message  = messaging.Message(
                data = {
                    "title": MsgTitle,
                    "body": MsgBody,
                    "ActionURL": ActionUrl
                },
                apns    = _apns,
                token   = deviceToken,
                android = _android
            )

            response = messaging.send(message)
            return response

        except messaging.UnregisteredError as UnregisteredError:
            logger.error(f"Unregistered token. Please refresh your FCM token:{str(UnregisteredError)}")
            return str(UnregisteredError)

        except Exception as e:
            logger.error(f"Push Exception: {str(e)}")
            return str(e)