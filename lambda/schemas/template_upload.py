from json import JSONEncoder


class TemplateAddRequest:
    def __init__(self, data):
        self.event = data['event']
        self.paymentType = data['paymenttype']
        self.actionBy = data['actionby']
        self.principalTemplateId = data['principaltemplateid']
        self.templateId = data['templateid']
        self.header = data['header']
        self.isSMS = data['issms']
        self.smsContent = data['smscontent']
        self.createdBy = data['createdby']
        self.isPush = data['ispush']
        self.pushTitle = data['pushtitle']
        self.pushContent = data['pushcontent']
        self.pushActionLink = data['pushactionlink']
        self.isEmail = data['isemail']
        self.emailSubject = data['emailsubject']
        self.emailContent = data['emailcontent']
        self.emailReceipient = data['emailreceipient']
        self.isWhatsapp = data['iswhatsapp']
        self.waTemplate = data['watemplate']
        self.waBody = data['wabody']
        self.waHeader = data['waheader']
        self.waButtons = data['wabuttons']
        self.createdAt = data['createdat']

class TemplateAddApiRequest:
    def __init__(self, data):
        self.data = data


class ParameterEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__