import traceback
from dal.template_dal import TemplateDal
from commons import Mongo, NotificationLogger
from biz.errors import NotFoundError
from dal.errors import IdempotencyError
from schemas.v1 import DalTemplateRequest, SuccessTemplateAddResponse
from schemas.v1 import SuccessTemplateResponse
from datetime import datetime, timedelta

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class NoSQLDal(TemplateDal):
    def __init__(self):
        super(NoSQLDal, self).__init__()
        self.__datastore = Mongo()

    def template_add(self, request: DalTemplateRequest, idempotency_key: str):
        dbname = self.__datastore.db()
        try:
            idempotency_items = list(dbname.template_pool.find({"EventId":idempotency_key}))
            if isinstance(idempotency_items, list) and len(idempotency_items) > 0:
                raise IdempotencyError(idempotency_items)
            
            dbname.template_pool.update_one({"EventId": str(idempotency_key)}, {"$set": request.dict()}, upsert=True)

            return SuccessTemplateAddResponse(
                EventId=idempotency_key,
                Event=request.Event,
                # SMSContent=request.SMSContent,
                # PushContent=request.PushContent,
                # EmailContent=request.EmailContent,
                status="success",
                message="Template added successfully"
            )
        except Exception as e:
            logger.error(e)
            raise e
        
    def get_event_template(self, eventId):
        dbname = self.__datastore.db()
        try:
            items = list(dbname.template_pool.find({"EventId":eventId},{"_id":0}))
            if isinstance(items, list) and len(items)== 0:
                msg = "Template not found for event id: {}".format(eventId)
                raise NotFoundError(message=msg)
            
            for item in items:
                return SuccessTemplateResponse(
                    EventId=item['EventId'],
                    Event=item['Event'],
                    PaymentType=item['PaymentType'],
                    ActionBy=item['ActionBy'],
                    PrincipalTemplateId=item['PrincipalTemplateId'],
                    TemplateId=item['TemplateId'],
                    Header=item['Header'],
                    IsSMS=item['IsSMS'],
                    SMSContent=item['SMSContent'],
                    IsPush=item['IsPush'],
                    PushTitle=item['PushTitle'],
                    PushContent=item['PushContent'],
                    PushActionLink=item['PushActionLink'],
                    IsEmail=item['IsEmail'],
                    EmailSubject=item['EmailSubject'],
                    EmailContent=item['EmailContent'],
                    EmailReceipient=item['EmailReceipient']
                )
        except Exception as e:
            logger.error(e)
            raise e

    def save_log(self, request: dict):
        dbname = self.__datastore.db()
        try:
            return dbname.notification_log.insert_one(request).inserted_id
        except Exception as e:
            logger.error(e)
            raise e
        
    def delete_old_logs(self):
        try:
            dbname = self.__datastore.db()
            logs = dbname.notification_log

            threshold_date = datetime.utcnow() - timedelta(days=3)
            result = logs.delete_many({"createdAt": {"$lt": threshold_date}})
            return result.deleted_count
        except Exception as e:
            logger.error(e)
            raise e