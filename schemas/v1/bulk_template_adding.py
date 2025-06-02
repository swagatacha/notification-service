from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Any


class TemplateAddRequest(BaseModel):
    event: str
    paymentType: Optional[str]
    actionBy: Optional[str]
    principalTemplateId: Optional[str]
    templateId: Optional[str]
    header: Optional[str]
    isSMS: str
    smsContent: Optional[str]
    createdBy: str
    isPush: str
    pushTitle: Optional[str]
    pushContent: Optional[str]
    pushActionLink: Optional[str]
    isEmail: str
    emailSubject: Optional[str]
    emailContent: Optional[str]
    emailReceipient: Optional[str]
    isWhatsapp: str
    waTemplate: Optional[str]
    waBody: Optional[str]
    waHeader: Optional[str]
    waButtons: Optional[str]
    isActive: bool = True
    createdAt: str

    @model_validator(mode="after")
    def validate_fields(self):
        errors = []

        if self.isSMS == 'Y':
            for field in ['templateId', 'principalTemplateId', 'header', 'smsContent']:
                if not getattr(self, field):
                    errors.append(f"{field} is required when isSMS is 'Y'")

        if self.isPush == 'Y':
            for field in ['pushTitle', 'pushContent', 'pushActionLink']:
                if not getattr(self, field):
                    errors.append(f"{field} is required when isPush is 'Y'")

        if self.isEmail == 'Y':
            for field in ['emailSubject', 'emailContent']:
                if not getattr(self, field):
                    errors.append(f"{field} is required when isEmail is 'Y'")

        if self.isWhatsapp == 'Y':
            for field in ['waTemplate', 'waBody']:
                if not getattr(self, field):
                    errors.append(f"{field} is required when isWhatsapp is 'Y'")

        if errors:
            raise ValueError("; ".join(errors))
        return self

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