from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel


class TemplateAddRequest(BaseModel):
    Event: str
    PaymentType: Optional[str]
    ActionBy: Optional[str]
    PrincipalTemplateId: Optional[str]
    TemplateId: str
    Header: str
    IsSMS: str
    SMSContent: str
    CreatedBy: str
    IsPush: str
    PushTitle: Optional[str]
    PushContent: Optional[str]
    PushActionLink: Optional[str]
    IsEmail: str
    EmailSubject: Optional[str]
    EmailContent: Optional[str]
    EmailReceipient: Optional[str]
    CreatedAt: str

class DalTemplateRequest(TemplateAddRequest):
    EventId: str

class TemplateAddBulkRequest(BaseModel):
    data: List[TemplateAddRequest]

class TemplateAddResponse:
    def __init__(self, Event):
        self.Event = Event

class TemplateAddResponseBase(BaseModel):
    EventId: str
    Event: str
    status: str
    message: Optional[str] = None

class SuccessTemplateAddResponse(TemplateAddResponseBase):
    SMSContent: str
    PushContent: Optional[str] = None
    EmailContent: Optional[str] = None
    
class FailureTemplateAddResponse(BaseModel):
    pass

class TemplateBulkResponse(BaseModel):
    status: str
    response: Any
    message: str

    def __init__(self, status, response, message):
        super(TemplateBulkResponse, self).__init__(status=status, response=response, message=message)