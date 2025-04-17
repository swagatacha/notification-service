from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel

class TemplateResponseBase(BaseModel):
    EventId: str
    Event: str


class SuccessTemplateResponse(TemplateResponseBase):
    PaymentType: Optional[str]
    ActionBy: Optional[str]
    PrincipalTemplateId: Optional[str]
    TemplateId: str
    Header: str
    IsSMS: str
    SMSContent: str
    IsPush: str
    PushTitle: Optional[str]
    PushContent: Optional[str]
    PushActionLink: Optional[str]
    IsEmail: str
    EmailSubject: Optional[str]
    EmailContent: Optional[str]
    EmailReceipient: Optional[str]