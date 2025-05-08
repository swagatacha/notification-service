from datetime import datetime
import json
from dal.errors import IdempotencyError
from dal.sql.sql_dal import NoSQLDal, NotificationLogger
from handlers.email_handler import Email
from handlers.sms_handler import Sms
from handlers.push_handler import Push
from schemas.v1 import TemplateAddBulkRequest, TemplateBulkResponse, FailureTemplateAddResponse
import traceback
from commons import config, TemplateValueMapper, RedisClient, EmailTemplateMapper
from datetime import datetime, timedelta

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

    def save_log(self, data: dict):
        self.__dal.save_log(data)

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
                    "orderId":message.get("orderid",''),
                    "response": json.dumps(resp),
                    "createdAt": datetime.utcnow()
                }
                self.save_log(data)
            return resp
        except Exception as e:
            logger.error(f"failed in send_notification:{traceback.format_exc()}")
            data={
                    "mobileNo": message.get("mobileno"),
                    "event": message.get("message_key"),
                    "orderId":message.get("orderid",''),
                    "response": str(e),
                    "createdAt": datetime.utcnow()
                }
            self.save_log(data)
            raise e
        
def is_same_day_multi_shipped(redis_client, message):

    updated_str = message.get("updateddate", "")
    updated_dt = datetime.strptime(updated_str, "%Y-%m-%dT%H:%M:%S.000Z")

    end_of_day = updated_dt.replace(hour=23, minute=59, second=59)
    ttl_seconds = int((end_of_day - datetime.utcnow()).total_seconds())

    date = message.get("updateddate","")[:10]
    daily_key = f"notified_shipments:{date}"
    member_id = f"{message['message_key']}:{message['mobileno']}"
    logger.info(f"checking for member {member_id} in daily key {daily_key}")
    
    if redis_client.sismember(daily_key, member_id):
        return True
    
    redis_client.sadd(daily_key, member_id)
    redis_client.expire(daily_key, ttl_seconds if ttl_seconds > 0 else 300)
    return False

def buffer_queue_fallback(redis_client, order_id, pending_hash_key):
    logger.info(f"Fallback triggered for order {order_id}. Checking buffered messages for age > 3 hours.")
    now = datetime.utcnow()

    for status, priority in sorted(config.STATUS_PRIORITY.items(), key=lambda x: x[1]):
        field = f"{order_id}:{status}"
        buffered_msg_raw = redis_client.hget(pending_hash_key, field)
        if not buffered_msg_raw:
            continue

        try:
            buffered_msg = json.loads(buffered_msg_raw)
            timestamp_str = buffered_msg.get("received_at")
            if not timestamp_str:
                logger.warning(f"Missing received_at in buffered message for {field}, skipping.")
                continue

            msg_time = datetime.utcfromtimestamp(timestamp_str)
            age = now - msg_time
            logger.info(f'age is {age}')

            if age >= timedelta(hours=3):
                logger.info(f"Processing stale buffered message {status} for order {order_id} (age: {age}).")
                redis_client.hdel(pending_hash_key, field)
                biz = NotificationBiz()
                biz.send_notification(buffered_msg.get('message'))
                redis_client.hset("notification_status_all", order_id, status)
            else:
                logger.info(f"Buffered message {status} for order {order_id} is too recent (age: {age}). Skipping.")

        except Exception as e:
            logger.error(f"Error while processing buffered message for {field}: {e}. Deleting to avoid blockage.")
            redis_client.hdel(pending_hash_key, field)

def order_state_consistency(redis_client, message):
    biz = NotificationBiz()
    order_id = message['orderid']
    new_status = message['message_key']
    new_priority = config.STATUS_PRIORITY[new_status]

    # Centralized Redis hash keys
    status_hash_key = "notification_status_all"
    pending_hash_key = "pending_notifications_all"

    # Fetch current status from the centralized hash
    current_status = redis_client.hget(status_hash_key, order_id)
    if isinstance(current_status, bytes):
        current_status = current_status.decode("utf-8")
    current_priority = config.STATUS_PRIORITY.get(current_status, 0)

    data = {
        "mobileNo": message.get("mobileno"),
        "event": new_status,
        "orderId": order_id,
        "createdAt": datetime.utcnow()
    }

    # Terminal state logic
    if current_status in config.TERMINATION_STATES and new_priority < current_priority:
        logger.info(f"Ignoring outdated {new_status} for order {order_id} (already in terminal state).")
        data['response'] = f"Ignoring outdated {new_status} for order {order_id} (already in terminal state)."
        biz.save_log(data)
        return

    if new_status in config.TERMINATION_STATES:
        logger.info(f"Processing terminal state {new_status} for order {order_id}, clearing pending.")
        biz.send_notification(message)
        redis_client.hset(status_hash_key, order_id, new_status)

        # Clean up all buffered statuses for this order
        for status in config.STATUS_PRIORITY.keys():
            redis_client.hdel(pending_hash_key, f"{order_id}:{status}")
        return

    if new_priority <= current_priority:
        logger.info(f"Skipping outdated or duplicate {new_status} for order {order_id}.")
        data['response'] = f"Skipping outdated or duplicate {new_status} for order {order_id}."
        biz.save_log(data)
        return

    if new_priority > current_priority + 1:
        logger.info(f"Buffering {new_status} for order {order_id}, waiting for earlier state.")
        buffered_entry = {
            "message": message,
            "received_at": int(datetime.utcnow().timestamp())
        }
        redis_client.hset(pending_hash_key, f"{order_id}:{new_status}", json.dumps(buffered_entry))
        data['response'] = f"Buffering {new_status} for order {order_id}, waiting for earlier state."
        biz.save_log(data)
        return

    # Special case: same-day shipment deduplication
    if new_status == "order_shipped":
        if is_same_day_multi_shipped(redis_client, message):
            logger.info(f"Shipment notification already sent for today. Skipping.")
            data['response'] = f"Shipment notification already sent for today. Skipping."
            biz.save_log(data)
            return

    # Send notification and update current status
    biz.send_notification(message)
    redis_client.hset(status_hash_key, order_id, new_status)

    # Try sending buffered next-status message if present
    next_priority = new_priority + 1
    for status, priority in config.STATUS_PRIORITY.items():
        if priority == next_priority:
            pending_field = f"{order_id}:{status}"
            buffered = redis_client.hget(pending_hash_key, pending_field)
            if buffered:
                buffered_obj = json.loads(buffered)
                message_to_send = buffered_obj.get('message')
                logger.info(f"Sending buffered {status} for order {order_id}.")
                redis_client.hdel(pending_hash_key, pending_field)
                if message_to_send:
                    order_state_consistency(redis_client, message_to_send)
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

