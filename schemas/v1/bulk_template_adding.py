from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel


class TemplateAddRequest(BaseModel):
    event: str
    paymentType: Optional[str]
    actionBy: Optional[str]
    principalTemplateId: Optional[str]
    templateId: str
    header: str
    isSMS: str
    smsContent: str
    createdBy: str
    isPush: str
    pushTitle: Optional[str]
    pushContent: Optional[str]
    pushActionLink: Optional[str]
    isEmail: str
    emailSubject: Optional[str]
    emailContent: Optional[str]
    emailReceipient: Optional[str]
    isWhatsapp:str
    waTemplate:Optional[str]
    waBody:Optional[str]
    waHeader:Optional[str]
    waButtons:Optional[str]
    isActive: bool = True
    createdAt: str

class DalTemplateRequest(TemplateAddRequest):
    eventId: str

class TemplateAddBulkRequest(BaseModel):
    data: List[TemplateAddRequest]

class TemplateAddResponse:
    def __init__(self, Event):
        self.Event = Event

class TemplateAddResponseBase(BaseModel):
    eventId: str
    event: str
    status: str
    message: Optional[str] = None

class SuccessTemplateAddResponse(TemplateAddResponseBase):
    smsContent: Optional[str] = None
    pushTitle: Optional[str] = None
    pushContent: Optional[str] = None
    emailSubject: Optional[str] = None
    emailContent: Optional[str] = None
    waBody: Optional[str]
    
class FailureTemplateAddResponse(TemplateAddResponseBase):
    pass

class TemplateBulkResponse(BaseModel):
    status: str
    response: Any
    message: str

    def __init__(self, status, response, message):
        super(TemplateBulkResponse, self).__init__(status=status, response=response, message=message)