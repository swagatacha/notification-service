import traceback
from fastapi import APIRouter, Response, HTTPException
from biz.errors import NotFoundError
from biz.notification_processor import NotificationBiz
from biz.template_processor import TemplateBiz
from schemas.v1.bulk_template_adding import TemplateAddBulkRequest, TemplateBulkResponse
from biz.notification_processor import process_message
from commons import NotificationLogger
from schemas.v1 import TemplateLists, TemplateDetails, TemplateModifyResponse, TemplateModifyRequest, ProviderDetail, ServiceProviders

log_clt = NotificationLogger()
logger = log_clt.get_logger()

router = APIRouter(
    prefix="/api/v1"
)
notification_biz = NotificationBiz()
template_biz = TemplateBiz()

@router.post("/batch/template/add", responses={200: {'model': TemplateBulkResponse}})
def template_bulk_upload(payload: TemplateAddBulkRequest, response: Response):
    try:
        logger.info(f"template batch upload payload is {payload}")
        batch_response = template_biz.template_bulk_add(payload)
        response.status_code = 200
        return {
            "data": batch_response
        }
    except Exception as e:
        logger.error(f"server error in batch upload processing {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
    

@router.get("/template/list", responses={200: {'model': TemplateLists}})
def get_templates(page_num: int, page_size: int, response: Response):
    try:
        all_response = template_biz.get_templates(page_num, page_size)
        response.status_code = 200
        return {
            "data": all_response
        }
    except NotFoundError as e:
        response.status_code = 404
        raise HTTPException(detail=f"Unable to process request:{e}", status_code=response.status_code)
    except Exception as e:
        logger.error(f"server error in fetch template listing {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail=f"Unable to process request", status_code=response.status_code)
    
@router.get("/template/details", responses={200: {'model': TemplateDetails}})
def get_templates(eventId: str, response: Response):
    try:
        details = template_biz.template_details(eventId)
        response.status_code = 200
        return {
            "data": details
        }
    except NotFoundError as e:
        response.status_code = 404
        raise HTTPException(detail=f"Unable to process request,{e}", status_code=response.status_code)
    except Exception as e:
        logger.error(f"server error in fetch template listing {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)

@router.post("/template/modify", responses={200: {'model': TemplateModifyResponse}})
def template_add_edit(payload: TemplateModifyRequest, response: Response):
    try:
        modify_response = template_biz.template_add_edit(payload)
        response.status_code = 200
        return {
            "data": modify_response
        }
    except Exception as e:
        logger.error(f"server error in batch upload processing {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
    
@router.post("/provider/add", responses={200: {'model': ServiceProviders}})
def service_provider_add(payload: ProviderDetail, response: Response):
    try:
        provider_resp = template_biz.service_provider_add(payload)
        response.status_code = 200
        return {
            "data": provider_resp
        }
    except Exception as e:
        logger.error(f"server error in add provider {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
    
@router.post("/webhook/dlr")
def notification_delivery_report(payload: dict, response: Response):
    try:
        if "results" in payload:
            reports = []
            for item in payload.get("results", []):
                reports.append({
                    "messageId": item["messageId"],
                    "status": item["status"]["name"],
                    "deliveredAt": item.get("doneAt")
                })
        elif "reference" in payload:
            data = {
                "messageId": payload["reference"],                
                "status": payload["status_code"],              
                "deliveredAt": payload.get("delivered")
            }
            reports = [data]
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider payload")
        
        notification_biz.update_sms_log(reports)

        response.status_code = 200
        return {
            "data": {"status": "DLRs processed"}
        }
    except Exception as e:
        logger.error(f"server error in add provider {traceback.format_exc()}")
        response.status_code = 500
        raise HTTPException(detail="Unable to process request", status_code=response.status_code)
    
@router.post("/notification/process", responses={200:{'model':TemplateBulkResponse}})
def notification_process(response: Response):
    try:
        test_message = {
                    "emailid": None,
                    "message_key": "order_placed",
                    "tags": [
                        "_parent_aggregated",
                        "_aggregateexception"
                    ],
                    "parentorderid": 101002480419,
                    "mobileno": 9051574010,
                    "onlinerefund": 0,
                    "orderamount": 378,
                    "updateddate": "2025-03-05T17:49:50.000Z",
                    "ordertype": "P",
                    "googleregid": "fQJzrQvkw3EjNmL5IZ-Zj_:APA91bGZvvztgu-bIMlVSeBgb6G2T_3pQ8IdLPODC7cyG9V_y0t5wlYbzE1nLf_zYsUpvlpYgBVzWjMyiW8xS8GznTWAXUSqqIWSH1H0lnsrt43h1JpmiPY",
                    "seen_orderids": [
                        101002480419
                    ],
                    "orderid": 101002480419,
                    "parentorder_agg_id": [
                        "101002480419",
                        "101002480419"
                    ],
                    "fullname": "sumik  ",
                    "walletrefund": 0,
                    "paymenttype": 1,
                    "order_count": 3,
                    "@timestamp": "2025-05-22T14:19:02.125700455Z",
                    "orderstatusid": 1,
                    "orderplacedby": "C",
                    "fname": "sumik",
                    "@version": "1",
                    "products": [
                        "Pan L Cap (10 Cap)",
                        "Pan 20 mg Tab (10 Tab)",
                        "Panbrom Eye Drop 5 ml"
                    ]
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
    
