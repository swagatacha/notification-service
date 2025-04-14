from json import JSONEncoder


class TemplateAddRequest:
    def __init__(self, data):
        self.Event = data['Event']
        self.PaymentType = data['PaymentType']
        self.ActionBy = data['ActionBy']
        self.TemplateId = data['TemplateId']
        self.Header = data['Header']
        self.SMSContent = data['SMSContent']
        self.CreatedBy = data['CreatedBy']
        self.PushContent = data['PushContent']
        self.EmailContent = data['EmailContent']
        self.CreatedAt = data['CreatedAt']

class TemplateAddApiRequest:
    def __init__(self, data):
        self.data = data


class ParameterEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__