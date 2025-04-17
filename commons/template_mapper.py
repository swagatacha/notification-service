class TemplateValueMapper:

    def __init__(self, message: dict):
        self.message = message

    def get_values(self) -> dict:
        return {
            "pname": self.message.get("fname", "Customer"),
            "orderamount": self.message.get("orderbillamount", ""),
            "orderid": self.message.get("orderid", ""),
            "products": self.message.get("productname", ""),
            "refundamount":self.message.get("refundamount", ""),
            "reason":self.message.get("reason", ""),
            "url":""
        }
    
    def format_template(self, template: str, values: dict) -> str:
        for key, val in values.items():
            template = template.replace(f"{{#{key}#}}", str(val))
        return template

