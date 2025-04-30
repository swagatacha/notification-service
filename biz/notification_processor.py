from datetime import datetime
import json
from dal.errors import IdempotencyError
from dal.sql.sql_dal import NoSQLDal, NotificationLogger
from handlers.email_handler import Email
from handlers.sms_handler import Sms
from handlers.push_handler import Push
from schemas.v1 import TemplateAddBulkRequest, TemplateBulkResponse, FailureTemplateAddResponse
import redis
import traceback
from commons import config, TemplateValueMapper, RedisClient, EmailTemplateMapper

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

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
                idempotent.append(TemplateValueMapper.formatted_event_id(client_request_id))
            except Exception as e:
                logger.error(e)
                failure.append(FailureTemplateAddResponse(
                        EventId=TemplateValueMapper.formatted_event_id(client_request_id),
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
    
    def template_mapping(self, msg, raw_data):
        value_mapper = TemplateValueMapper(msg)
        template_values = value_mapper.get_values()
        formatted_content = value_mapper.format_template(raw_data, template_values)
        return formatted_content
    
    def generate_eventid_from_msg(self, message):
        message_key = message.get("message_key")
        if "order_edit_agg_id" in message:
                orderplacedby = "B" if message.get("orderplacedby") == "O" else  message.get("orderplacedby")
                ordertype = ''
                paymentType = str(message.get("paymenttype",""))
                parts = [message_key, paymentType, ordertype, orderplacedby] 
        elif "order_agg_id" in message and int(message.get("orderstatusid")) == 8 :
            orderplacedby = "B" if message.get("orderplacedby") == "O" else  message.get("orderplacedby")
            ordertype = "M" if message.get("ordertype") == "P" else  message.get("ordertype")
            ordertype = ''
            paymentType = str(message.get("paymenttype",""))
            parts = [message_key, paymentType, ordertype, orderplacedby] 
        else:
            parts = [message_key]

        client_request_id = "_".join(filter(None, parts))
        return client_request_id


    def send_notification(self, message:dict):
        try:
            template_data = self.__dal.get_event_template(self.generate_eventid_from_msg(message))

            mobileno = message.get("mobileno")
            is_sms = template_data.IsSMS
            is_push = template_data.IsPush
            is_email = template_data.IsEmail

            resp = {}

            if is_sms == 'Y':
                active_provider = config.ACTIVE_SMS_PROVIDER
                sms_header = template_data.Header
                sms_content = self.template_mapping(message, template_data.SMSContent)

                if active_provider == 'INFOBIP':
                    resp['sms'] = Sms(sms_header).send_sms_infobip(sms_content, mobileno,
                                                            template_data.PrincipalTemplateId, template_data.TemplateId)
                elif active_provider == 'TEXTNATION':
                    resp['sms'] = Sms(sms_header).send_sms_connectexpress(sms_content, mobileno)
                else:
                    resp['sms'] = Sms(sms_header).send_sms_vfirst(sms_content, mobileno)

            if is_push == 'Y':
                push_content = self.template_mapping(message, template_data.PushContent)

                notification_details = {
                    "token": message.get("GCMKey", ""),
                    "PushTitle": template_data.PushTitle,
                    "PushContent": push_content,
                    "ActionLink": template_data.PushActionLink
                }
                resp['push'] = Push().send_push(notification_details)

            if is_email == 'Y':
                email_content = self.template_mapping(message, template_data.EmailContent)
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
            data={
                    "mobileNo": message.get("mobileno"),
                    "event": message.get("message_key"),
                    "response": str(e),
                    "createdAt": datetime.utcnow()
                }
            self.__dal.save_log(data)
            raise e
        
def is_same_day_multi_shipped(redis_client, message):

    updated_str = message.get("updateddate", "")
    updated_dt = datetime.strptime(updated_str, "%Y-%m-%dT%H:%M:%S.000Z")

    end_of_day = updated_dt.replace(hour=23, minute=59, second=59)
    ttl_seconds = int((end_of_day - datetime.utcnow()).total_seconds())

    date = message.get("updateddate","")[:10]
    redis_key = f"notif:{message['message_key']}:{message['mobileno']}:{date}"
    logger.info(f"redis key: {redis_key}") 
    if not redis_client.exists(redis_key):
        redis_client.setex(redis_key, ttl_seconds if ttl_seconds > 0 else 300, json.dumps(message))
        return False
    return True

def order_state_consistency(redis_client, message):
    biz = NotificationBiz()
    order_id = message['orderid']
    new_status = message['message_key']
    new_priority = config.STATUS_PRIORITY[new_status]

    redis_key = f"notification_status:{order_id}"
    pending_key = f"pending_notifications:{order_id}"

    current_status = redis_client.get(redis_key)
    current_priority = config.STATUS_PRIORITY.get(current_status, 0)

    if current_status in config.TERMINATION_STATES and new_priority < current_priority:
        logger.info(f"Ignoring outdated {new_status} for order {order_id} (already in terminal state).")
        return
    
    if new_status in config.TERMINATION_STATES:
        logger.info(f"Processing terminal state {new_status} for order {order_id}, clearing pending.")
        biz.send_notification(message)
        redis_client.set(redis_key, new_status)
        redis_client.delete(pending_key)
        return
    
    if new_priority <= current_priority:
        logger.info(f"Skipping outdated or duplicate {new_status} for order {order_id}.")
        return
    
    if new_priority > current_priority + 1:
        logger.info(f"Buffering {new_status} for order {order_id}, waiting for earlier state.")
        redis_client.hset(pending_key, new_status, json.dumps(message))
        return
    
    if new_status == "order_shipped":
        if is_same_day_multi_shipped(redis_client, message):
            logger.info(f"Shipment notification already sent for today. Skipping.")
            return
    
    biz.send_notification(message)
    redis_client.set(redis_key, new_status)

    next_priority = new_priority + 1
    for status, priority in config.STATUS_PRIORITY.items():
        if priority == next_priority:
            buffered = redis_client.hget(pending_key, status)
            if buffered:
                logger.info(f"Sending buffered {status} for order {order_id}.")
                redis_client.hdel(pending_key, status)
                order_state_consistency(redis_client, json.loads(buffered))
            break

def process_message(message):
    """
    Process the message and send notifications accordingly.
    """
    try:
        redis_client = RedisClient().get_client()
        if "order_agg_id" in message or "parentorder_agg_id" in message :
            order_state_consistency(redis_client, message)
        else:
            NotificationBiz().send_notification(message)
    except Exception as e:
        logger.error(f"failed to process message: {traceback.format_exc()}")
        raise e

