from datetime import datetime
import json
from biz.errors import NotFoundError
from dal.errors import IdempotencyError
from dal.sql.sql_dal import NoSQLDal, NotificationLogger
from handlers.email_handler import Email
from handlers.sms_handler import Sms
from handlers.push_handler import Push
from handlers.whatsapp_handler import Whatsapp
from schemas.v1 import TemplateAddBulkRequest, TemplateBulkResponse, FailureTemplateAddResponse, TemplateLists, TemplateDetails
from schemas.v1 import TemplateModifyResponse, SuccessTemplateModifyResponse, FailureTemplateModifyResponse, TemplateModifyRequest
from commons import config, TemplateValueMapper, RedisClient, EmailTemplateMapper
from datetime import datetime, timedelta
import re

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
            client_request_id_parts = [val.event]
            client_request_id_parts += [part for part in [val.paymentType, val.actionBy] if part is not None]
            client_request_id = "_".join(client_request_id_parts)
            try:
                credit_response = self.__dal.template_add(val, client_request_id)
                success.append(credit_response)
            except IdempotencyError as idempotent_error:
                idempotent.append(TemplateValueMapper.formatted_event_id(client_request_id))
            except Exception as e:
                logger.error(e)
                failure.append(FailureTemplateAddResponse(
                        eventId=TemplateValueMapper.formatted_event_id(client_request_id),
                        event=val.event,
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
    
    def template_add_edit(self, request:TemplateModifyRequest) -> TemplateModifyResponse:
        try:
            result= self.__dal.template_modify(request)
            logger.info(f'modify result:{result}')
            if result['matched_count'] == 0:
                return FailureTemplateModifyResponse(
                        eventId=request.eventId,
                        event=request.event,
                        status="error",
                        message="Document not found"
                    )
            elif result['modified_count'] == 0:
                return FailureTemplateModifyResponse(
                        eventId=request.eventId,
                        event=request.event,
                        status="error",
                        message="Document not modified"
                )
            else:
                return SuccessTemplateModifyResponse(                    
                    eventId=request.eventId,
                    event=request.event,
                    status="success",
                    message="Template Updated Successfully")
        except Exception as e:
            logger.error(e)
            raise FailureTemplateModifyResponse(
                    eventId=request.eventId,
                    event=request.event,
                    status="failure",
                    message=str(e)
                )

    
    def get_templates(self, page_num: int, page_size: int) -> TemplateLists:
        try:
            records = self.__dal.get_templates(page_num, page_size)

            for i in range(len(records['templates'])):
                records['templates'][i]['paymentType'] = TemplateValueMapper.formatted_payment_type(records['templates'][i]['paymentType']) if records['templates'][i]['paymentType'] is not None else records['templates'][i]['paymentType']
                records['templates'][i]['actionBy'] = TemplateValueMapper.formatted_action_by(records['templates'][i]['actionBy']) if records['templates'][i]['actionBy'] is not None else records['templates'][i]['actionBy']

            return TemplateLists(
                    templates=records['templates'],
                    page=page_num,
                    page_size=page_size,
                    total_count = records['total_count']
                )
        except NotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f'failed to fetch template list:{e}')
            raise e
    
    def template_details(self, eventId) -> TemplateDetails:
        try:
            template_data = self.__dal.get_template_details(eventId)
            template_data.paymentType = TemplateValueMapper.formatted_payment_type(template_data.paymentType)
            template_data.actionBy = TemplateValueMapper.formatted_action_by(template_data.actionBy)
            return TemplateDetails(details=template_data)
        except NotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f'failed to fetch template details:{e}')
            raise e

    def template_mapping(self, msg, raw_data):
        value_mapper = TemplateValueMapper(msg)
        template_values = value_mapper.get_values()
        formatted_content = value_mapper.format_template(raw_data, template_values)
        return formatted_content
    
    def placeholder_mapping(self, msg, placeholders):
        value_mapper = TemplateValueMapper(msg)
        template_values = value_mapper.get_values()
        if not placeholders:
            return []
        values_list = [template_values.get(key, "") for key in placeholders]
        return values_list
    
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

    def get_provider_info(self):
        provider_info = self.__dal.get_provider_info()

        if not provider_info:
            return config.ACTIVE_SMS_PROVIDER.lower()
        for provider in provider_info:
            if provider.get('isActive'):
                provider_name = provider.get('name', '')
                return provider_name.lower()
        
        return config.ACTIVE_SMS_PROVIDER.lower()

    def call_sms_handler(self, active_provider, message, template_data):
        sms_header = template_data.header
        sms_content = self.template_mapping(message, template_data.smsContent)
        mobileno = message.get("mobileno")
        data={
            "mobileNo": mobileno,
            "event": message.get("message_key"),
            "orderId":message.get("orderid",''),
            "channel":"sms",
            "service_provider": active_provider,
            "createdAt": datetime.utcnow()
        }
        try:
            if active_provider == 'infobip':
                response, status_code = Sms(sms_header).send_sms_infobip(sms_content, mobileno,
                                                                template_data.principalTemplateId, template_data.templateId)
                if status_code == 200 and 'messages' in response:
                    data['message_id'] = response['messages']['messageId']
                    data['http_status'] = status_code
                    data['groupId'] = response['messages']['status']['groupId']
                    data['status'] = response['messages']['status']['groupName']
                elif 'requestError' in response:
                    data['message_id'] = response['requestError']['serviceException']['messageId']
                    data['http_status'] = status_code
                    data['status'] = response['requestError']['serviceException']['text']
            elif active_provider == 'textnation':
                response, status_code  = Sms(sms_header).send_sms_connectexpress(sms_content, mobileno)
                if status_code == 200 and 'data' in response:
                    data['message_id'] = response['data'][0]['id']
                    data['http_status'] = status_code
                    data['groupId'] = response['data']['group_id']
                    data['status'] = response['data'][0]['status]']
                else:
                    data['status'] = response['status']
            else:
                response, status_code  = Sms(sms_header).send_sms_vfirst(sms_content, mobileno)

            self.save_log(data)
        except Exception as e:
            data['status'] = str(e)
            self.save_log(data)

    def call_push_handler(self, message, template_data):
        data={
                "mobileNo": message.get("mobileno"),
                "event": message.get("message_key"),
                "orderId":message.get("orderid",''),
                "channel":"push",
                "createdAt": datetime.utcnow()
            }
        try:
            push_content = self.template_mapping(message, template_data.pushContent)

            notification_details = {
                "token": message.get("GCMKey", ""),
                "PushTitle": template_data.pushTitle,
                "PushContent": push_content,
                "ActionLink": template_data.pushActionLink
            }
            push_resp = Push().send_push(notification_details)

            data['http_status'] = push_resp['status_code']
            data['status'] = push_resp['response']
            self.save_log(data)

        except Exception as e:
            data['status'] = str(e)
            self.save_log(data)

    def call_email_handler(self, message, template_data):
        data={
                "mobileNo": message.get("mobileno"),
                "emailId": message.get("emailid", ""),
                "event": message.get("message_key"),
                "orderId":message.get("orderid",''),
                "channel":"email",
                "createdAt": datetime.utcnow()
            }
        try:          
            email_content = self.template_mapping(message, template_data.emailContent)
            email_receipient = template_data.emailReceipient if template_data.emailReceipient is not None else message.get("emailid", "")

            email_resp = Email().mail(EmailTemplateMapper().buildhtml(email_content), template_data.emailSubject, email_receipient)
            data['status'] = email_resp
            self.save_log(data)

        except Exception as e:
            data['status'] = str(e)
            self.save_log(data)

    def call_wa_handler(self, active_provider, message, template_data):
        mobileno = message.get("mobileno")
        data={
            "mobileNo": mobileno,
            "event": message.get("message_key"),
            "orderId":message.get("orderid",''),
            "channel":"whatsapp",
            "service_provider": active_provider,
            "createdAt": datetime.utcnow()
        }

        try:
            placeholders = re.findall(r"{#(.*?)#}", template_data.waBody)
            body_content = self.placeholder_mapping(message, placeholders)
            template_name = template_data.waTemplate
            header_content = json.loads(template_data.waHeader)
            buttons_content = json.loads(template_data.waButtons)

            if active_provider == 'infobip':
                wa_resp = Whatsapp().send_wa_infobip(template_name, header_content, body_content, buttons_content, mobileno)
            elif active_provider == 'textnation':
                wa_resp = Whatsapp().send_wa_connectexpress(template_name, header_content, body_content, mobileno)
            self.save_log(data)
        except Exception as e:
            data['status'] = str(e)
            self.save_log(data)

    def send_notification(self, message:dict):
        try:
            template_data = self.__dal.get_template_details(self.generate_eventid_from_msg(message))

            is_sms = template_data.isSMS
            is_push = template_data.isPush
            is_email = template_data.isEmail
            is_wa = template_data.isWhatsapp
            active_provider = self.get_provider_info()

            if str(is_sms).upper() == 'Y':
                self.call_sms_handler(active_provider, message, template_data)
            if str(is_push).upper() == 'Y':
                self.call_push_handler(message, template_data)
            if str(is_email).upper() == 'Y':
                self.call_email_handler(message, template_data)
            if str(is_wa).upper() == 'Y':
                self.call_wa_handler(active_provider, message, template_data)

        except Exception as e:
            logger.error(f"failed in send_notification:{e}")
            data={
                    "mobileNo": message.get("mobileno"),
                    "event": message.get("message_key"),
                    "orderId":message.get("orderid",''),
                    "status": str(e),
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
    logger.info(f"Fallback triggered for order {order_id}. Checking buffered messages older than 3 hours.")
    now = datetime.utcnow()
    status_hash_key = "notification_status_all"
    biz = NotificationBiz()
    statuses = list(config.STATUS_PRIORITY.keys())

    for status, priority in sorted(config.STATUS_PRIORITY.items(), key=lambda x: x[1]):
        field = f"{order_id}:{status}"
        buffered_msg_raw = redis_client.hget(pending_hash_key, field)
        if not buffered_msg_raw:
            continue

        try:
            buffered_msg = json.loads(buffered_msg_raw)
            received_at = buffered_msg.get("received_at")
            message = buffered_msg.get("message")

            if not received_at or not message:
                logger.warning(f"Incomplete buffered message for {field}, skipping.")
                redis_client.hdel(pending_hash_key, field)
                continue

            msg_time = datetime.utcfromtimestamp(received_at)
            age = now - msg_time

            if status in config.TERMINATION_STATES:
                logger.info(f"Terminal state {status} found for order {order_id}. Processing immediately.")
                biz.send_notification(message)
                pipe = redis_client.pipeline()
                pipe.hdel(pending_hash_key, field)
                pipe.hset(status_hash_key, order_id, status)
                pipe.execute()
                
                # Clean up all buffered statuses for this order
                for s in statuses:
                    redis_client.hdel(pending_hash_key, f"{order_id}:{s}")
                return  # Stop processing any further statuses

            if age < timedelta(hours=3):
                logger.warning(f"Buffered message {status} for order {order_id} is too recent (age: {age}). Skipping.")
                continue

            if status == "order_shipped" and is_same_day_multi_shipped(redis_client, message):
                logger.info(f"Shipment notification already sent today for order {order_id}. Skipping.")
                continue

            logger.info(f"Processing stale buffered message {status} for order {order_id} (age: {age}).")
            biz.send_notification(message)
            pipe = redis_client.pipeline()
            pipe.hdel(pending_hash_key, field)
            pipe.hset(status_hash_key, order_id, status)
            pipe.execute()

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
        logger.error(f"failed to process message: {e}")
        raise e

