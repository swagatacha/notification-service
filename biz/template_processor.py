from datetime import datetime
import json
from biz.errors import NotFoundError
from dal.errors import IdempotencyError
from dal.sql.sql_dal import NoSQLDal, NotificationLogger
from schemas.v1 import TemplateAddBulkRequest, TemplateBulkResponse, FailureTemplateAddResponse, TemplateLists, TemplateDetails, DalProviderDetail
from schemas.v1 import TemplateModifyResponse, SuccessTemplateModifyResponse, FailureTemplateModifyResponse, TemplateModifyRequest, ProviderDetail, ServiceProviders
from commons import TemplateValueMapper
from datetime import datetime
import re

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class TemplateBiz:
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

    def service_provider_add(self, request:ProviderDetail):
        try:
            data = request.dict()
            data['name'] = data['name'].lower()
            data['CreatedAt'] = datetime.utcnow().isoformat()
            dal_request = DalProviderDetail(**data)

            result = self.__dal.service_provider_add(dal_request) 
            providers = [ProviderDetail(**{
                            "name": r["name"],
                            "isActive": r["isActive"],
                            "createdBy": r["createdBy"]
                        }) for r in result] 
            
            return ServiceProviders(providerList=providers)
        except Exception as e:
            raise e