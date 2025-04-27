from datetime import datetime
import json
from dal.errors import IdempotencyError
from dal.sql.sql_dal import NoSQLDal, logger
from handlers.email_handler import Email
from handlers.sms_handler import Sms
from handlers.push_handler import Push
from schemas.v1 import TemplateAddBulkRequest, TemplateBulkResponse, FailureTemplateAddResponse
import redis
import traceback
from commons import config, TemplateValueMapper, RedisClient, EmailTemplateMapper


class NotificationBiz:
    def __init__(self):
        self.__dal = NoSQLDal()

    def template_bulk_add(self, request: TemplateAddBulkRequest) -> TemplateBulkResponse:
        success = []
        failure = []
        idempotent = []
        status = ''

        for val in request.data:
            client_request_id_parts = [val.Event]
            client_request_id_parts += [part for part in [val.PaymentType, val.OrderType, val.ActionBy] if part is not None]
            client_request_id = "_".join(client_request_id_parts)
            try:
                credit_response = self.__dal.template_add(val, client_request_id)
                success.append(credit_response)
            except IdempotencyError as idempotent_error:
                logger.error(idempotent_error)
                idempotent.append(val.Event)
            except Exception as e:
                logger.error(e)
                failure.append(FailureTemplateAddResponse(
                        EventId=client_request_id,
                        Event=val.Event,
                        status="failure",
                        message=str(e)
                    ))

        if len(failure) == 0:
            status = "success"
        elif len(failure) == len(request.data):
            status = "failed"
        else:
            status = "partial"

        record = TemplateBulkResponse(status, {
            "success": success,
            "failed": failure,
            "idempotent": idempotent
        }, message="")

        return record

    def send_notification(self, message:dict):
        try:
            message_key = message.get("message_key")
            if "orderstatusid" not in message:
                orderplacedby = "B" if message.get("orderplacedby") == "O" else  message.get("orderplacedby")
                ordertype = "M" if message.get("ordertype") == "P" else  message.get("ordertype")
                ordertype = ''
                paymentType = str(message.get("paymenttype",""))
                parts = [message_key, paymentType, ordertype, orderplacedby] 
            elif int(message.get("orderstatusid")) == 8 :
                orderplacedby = "B" if message.get("orderplacedby") == "O" else  message.get("orderplacedby")
                ordertype = "M" if message.get("ordertype") == "P" else  message.get("ordertype")
                ordertype = ''
                paymentType = str(message.get("paymenttype",""))
                parts = [message_key, paymentType, ordertype, orderplacedby] 
            else:
                parts = [message_key]

            client_request_id = "_".join(filter(None, parts))

            template_data = self.__dal.get_event_template(client_request_id)

            mobileno = message.get("mobileno")
            is_sms = template_data.IsSMS
            is_push = template_data.IsPush
            is_email = template_data.IsEmail
            sms_content = template_data.SMSContent
            sms_header = template_data.Header
            resp = {}

            if is_sms == 'Y':
                active_provider = config.ACTIVE_SMS_PROVIDER
                value_mapper = TemplateValueMapper(message)
                template_values = value_mapper.get_values()
                sms_content = value_mapper.format_template(sms_content, template_values)

                if active_provider == 'INFOBIP':
                    resp['sms'] = Sms(sms_header).send_sms_infobip(sms_content, mobileno,
                                                            template_data.PrincipalTemplateId, template_data.TemplateId)
                elif active_provider == 'TEXTNATION':
                    resp['sms'] = Sms(sms_header).send_sms_connectexpress(sms_content, mobileno)
                else:
                    resp['sms'] = Sms(sms_header).send_sms_vfirst(sms_content, mobileno)

            if is_push == 'Y':
                notification_details = {
                    "token": message.get("GCMKey", ""),
                    "PushTitle": template_data.PushTitle,
                    "PushContent": template_data.PushContent,
                    "ActionLink": template_data.PushActionLink
                }
                resp['push'] = Push().send_push(notification_details)

            if is_email == 'Y':
                value_mapper = TemplateValueMapper(template_data.EmailContent)
                template_values = value_mapper.get_values()
                email_content = value_mapper.format_template(template_data.EmailContent, template_values)
                email_receipient = template_data.EmailReceipient if template_data.EmailReceipient is not None else message.get("emailid", "")
                resp['email'] = Email().mail(EmailTemplateMapper().buildhtml(email_content), template_data.EmailSubject, email_receipient)

            if resp:
                data={
                    "mobileNo": mobileno,
                    "event": message.get("message_key"),
                    "response": json.dumps(resp),
                    "createdAt": datetime.utcnow()
                }
                self.__dal.save_log(data)
            return resp
        except Exception as e:
            logger.error(f"failed in send_notification:{traceback.format_exc()}")
            raise e

def process_message(message):
    """
    Process the message and send notifications accordingly.
    """
    try:
        redis_client = RedisClient().get_client()
        if message.get("message_key") == "order_shipped":
            updated_str = message.get("updateddate", "")
            updated_dt = datetime.strptime(updated_str, "%Y-%m-%dT%H:%M:%S.000Z")

            end_of_day = updated_dt.replace(hour=23, minute=59, second=59)
            ttl_seconds = int((end_of_day - datetime.utcnow()).total_seconds())

            date = message.get("updateddate","")[:10]
            message_key = message.get("message_key")
            mobile_no = message.get("mobileno")
            redis_key = f"notif:{message_key}:{mobile_no}:{date}"
            logger.info(f"redis key: {redis_key}")
            if not redis_client.exists(redis_key):
                redis_client.setex(redis_key, ttl_seconds if ttl_seconds > 0 else 300, json.dumps(message))
                NotificationBiz().send_notification(message)
        else:
            NotificationBiz().send_notification(message)
    except Exception as e:
        logger.error(f"failed to process message: {traceback.format_exc()}")
        raise e

