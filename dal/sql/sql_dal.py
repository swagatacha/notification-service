import traceback
from dal.template_dal import TemplateDal
from commons import Mongo, NotificationLogger, TemplateValueMapper
from biz.errors import NotFoundError
from dal.errors import IdempotencyError
from schemas.v1 import DalTemplateRequest, SuccessTemplateAddResponse, SuccessTemplateResponse, DalTemplateModifyRequest
from datetime import datetime, timedelta

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class NoSQLDal(TemplateDal):
    def __init__(self):
        super(NoSQLDal, self).__init__()
        self.__datastore = Mongo()
    
    def get_provider_info(self):
        dbname = self.__datastore.db()
        try:
            items = list(dbname.provider_info.find({"_id":0}))
            return items
        except Exception as e:
            raise e

    def template_add(self, request: DalTemplateRequest, idempotency_key: str):
        dbname = self.__datastore.db()
        try:
            idempotency_items = list(dbname.template_pool.find({"eventId":idempotency_key}))
            if isinstance(idempotency_items, list) and len(idempotency_items) > 0:
                raise IdempotencyError(idempotency_items)
            
            request.isActive = True
            dbname.template_pool.update_one({"eventId": str(idempotency_key)}, {"$set": request.dict()}, upsert=True)

            return SuccessTemplateAddResponse(
                eventId=TemplateValueMapper.formatted_event_id(idempotency_key),
                event=request.event,
                smsContent=request.smsContent,
                pushTitle=request.pushTitle,
                pushContent=request.pushContent,
                emailSubject=request.emailSubject,
                emailContent=request.emailContent,
                waBody=request.waBody,
                status="success",
                message="Template added successfully"
            )
        except Exception as e:
            raise e
        
    def template_modify(self, request: DalTemplateModifyRequest):
        dbname = self.__datastore.db()
        try:

            update_data = {
                k: v for k, v in request.dict().items()
                if k not in ["Event", "CreatedAt", "CreatedBy"] and v not in [None, "", []]
            }
            update_data['UpdatedAt'] = datetime.utcnow()
            logger.info(f'update_data:{update_data}')
            result = dbname.template_pool.update_one({"eventId": str(request.eventId)}, {"$set": update_data}, upsert=False)
            return {'matched_count': result.matched_count, 'modified_count': result.modified_count}
        except Exception as e:
            raise e
        
    def get_template_details(self, eventId):
        dbname = self.__datastore.db()
        try:
            items = list(dbname.template_pool.find({"eventId":eventId},{"_id":0}))
            if isinstance(items, list) and len(items)== 0:
                msg = "Template not found for event id: {}".format(eventId)
                raise NotFoundError(message=msg)
            logger.info(f'get_template_details:{items}')
            for item in items:
                return SuccessTemplateResponse(
                    eventId=item['eventId'],
                    event=item['event'],
                    paymentType=item['paymentType'],
                    actionBy=item['actionBy'],
                    principalTemplateId=item['principalTemplateId'],
                    templateId=item['templateId'],
                    header=item['header'],
                    isSMS=item['isSMS'],
                    smsContent=item['smsContent'],
                    isPush=item['isPush'],
                    pushTitle=item['pushTitle'],
                    pushContent=item['pushContent'],
                    pushActionLink=item['pushActionLink'],
                    isEmail=item['isEmail'],
                    emailSubject=item['emailSubject'],
                    emailContent=item['emailContent'],
                    emailReceipient=item['emailReceipient'],
                    isWhatsapp=item['isWhatsapp'],
                    waTemplate=item['waTemplate'],
                    waBody=item['waBody'],
                    waHeader=item['waHeader'],
                    waButtons=item['waButtons'],
                    isActive=item['isActive']
                )
        except Exception as e:
            logger.error(e)
            raise e

    def get_templates(self, page_num, page_size):
        dbname = self.__datastore.db()
        try:
            resp = {}
            skip_count = (page_num - 1) * page_size
            total_count = dbname.template_pool.count_documents({})
            items = list(dbname.template_pool.find({},{"_id":0}).skip(skip_count).limit(page_size))
            if isinstance(items, list) and len(items)== 0:
                raise NotFoundError(message="No Templates found")
            
            resp['templates'] = items
            resp['total_count'] = total_count
            return resp
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
        
    