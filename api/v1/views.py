import traceback
from fastapi import APIRouter, Response, HTTPException
from biz.notification_processor import NotificationBiz
from schemas.v1.bulk_template_adding import TemplateAddBulkRequest, TemplateBulkResponse
from biz.notification_processor import process_message
from commons import NotificationLogger

log_clt = NotificationLogger()
logger = log_clt.get_logger()

router = APIRouter(
    prefix="/api/v1"
)
notification_biz = NotificationBiz()

@router.post("/batch/template/add", responses={200: {'model': TemplateBulkResponse}})
def template_bulk_upload(payload: TemplateAddBulkRequest, response: Response):
    try:
        logger.info(f"template batch upload payload is {payload}")
        batch_response = notification_biz.template_bulk_add(payload)
        response.status_code = 200
        return {
            "data": batch_response
        }
    except Exception as e:
        logger.error(f"server error in batch upload processing {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
    
@router.post("/notification/process", responses={200:{'model':TemplateBulkResponse}})
def notification_process(response: Response):
    try:
        test_message = {
            'fname': 'Madhurima',
            '@timestamp': '2025-04-14T10:04:01.489133506Z',
            'emailid': 'ranju.test@gmail.com',
            'orderid': 101000070498,
            'paymentType':None,
            'orderBy': None,
            'message_key': 'order_confirmed',
            '@version': '1',
            'orderstatusid': 2,
            'updateddate': '2025-03-31T16:18:47.000Z',
            'fullname': 'Madhurima d',
            'mobileno': '6292198784'
        }
        record = process_message(test_message)
        response.status_code = 200
        return {
            "data":"processed",
            "payload":record
        }
    except Exception as e:
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
