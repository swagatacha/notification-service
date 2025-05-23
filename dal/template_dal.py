from schemas.v1.bulk_template_adding import DalTemplateRequest


class TemplateDal:
    def __init__(self):
        pass

    def template_add(self, request: DalTemplateRequest, idempotency_key: str):
        pass

    def get_template_details(self, eventId:str):
        pass

    def template_modify(self, request: DalTemplateRequest):
        pass

    def get_template_details(self, eventId:str):
        pass

    def get_templates(self, page_num:int, page_size:int):
        pass

    def save_log(self, request: dict):
        pass
