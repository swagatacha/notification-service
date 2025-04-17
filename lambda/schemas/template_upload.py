from json import JSONEncoder


class TemplateAddRequest:
    def __init__(self, data):
        self.Event = data['Event']
        self.PaymentType = data['PaymentType']
        self.ActionBy = data['ActionBy']
        self.PrincipalTemplateId = data['PrincipalTemplateId']
        self.TemplateId = data['TemplateId']
        self.Header = data['Header']
        self.IsSMS = data['IsSMS']
        self.SMSContent = data['SMSContent']
        self.CreatedBy = data['CreatedBy']
        self.IsPush = data['IsPush']
        self.PushTitle = data['PushTitle']
        self.PushContent = data['PushContent']
        self.PushActionLink = data['PushActionLink']
        self.IsEmail = data['IsEmail']
        self.EmailSubject = data['EmailSubject']
        self.EmailContent = data['EmailContent']
        self.EmailReceipient = data['EmailReceipient']
        self.CreatedAt = data['CreatedAt']

class TemplateAddApiRequest:
    def __init__(self, data):
        self.data = data


class ParameterEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__