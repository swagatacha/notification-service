from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel

class TemplateModifyRequest(BaseModel):
    eventId: str
    event: str
    paymentType: Optional[str] = None
    actionBy: Optional[str] = None
    principalTemplateId: Optional[str] = None
    templateId: Optional[str] = None
    header: Optional[str]= None
    isSMS: Optional[str]= None
    smsContent: Optional[str]= None
    updatedBy: str
    isPush: Optional[str]= None
    pushTitle: Optional[str]= None
    pushContent: Optional[str]= None
    pushActionLink: Optional[str]= None
    isEmail: Optional[str]= None
    emailSubject: Optional[str]= None
    emailContent: Optional[str]= None
    emailReceipient: Optional[str]= None
    isWhatsapp:Optional[str]= None
    waTemplate:Optional[str]=None
    waBody:Optional[str]= None
    waHeader:Optional[str]= None
    waButtons:Optional[str]= None
    isActive: bool = True

class DalTemplateModifyRequest(TemplateModifyRequest):
    updatedAt:str

class TemplateModifyResponse(BaseModel):
    eventId: str
    event: str
    status: str
    message: str

class SuccessTemplateModifyResponse(TemplateModifyResponse):
    pass
    
class FailureTemplateModifyResponse(TemplateModifyResponse):
    pass