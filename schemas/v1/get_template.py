from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel

class TemplateResponseBase(BaseModel):
    eventId: str
    event: str


class SuccessTemplateResponse(TemplateResponseBase):
    paymentType: Optional[str] =None
    actionBy: Optional[str] = None
    principalTemplateId: Optional[str] = None
    templateId: str
    header: str
    isSMS: str
    smsContent: str
    isPush: str
    pushTitle: Optional[str] = None
    pushContent: Optional[str] = None
    pushActionLink: Optional[str] = None
    isEmail: str
    emailSubject: Optional[str] = None
    emailContent: Optional[str] = None
    emailReceipient: Optional[str] = None
    isWhatsapp: str
    waTemplate:Optional[str] = None
    waBody:Optional[str] = None
    waHeader:Optional[str] = None
    waButtons:Optional[str] = None
    isActive: bool

class TemplateLists(BaseModel):
    templates: List[SuccessTemplateResponse]
    page:int
    page_size:int
    total_count:int

class TemplateDetails(BaseModel):
    details:SuccessTemplateResponse