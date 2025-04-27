import base64

class TemplateValueMapper:

    def __init__(self, message: dict):
        self.message = message

    def get_values(self) -> dict:
        return {
            "pname": self.message.get("fname", "Customer"),
            "orderamount": self.message.get("orderbillamount", ""),
            "orderid": self.message.get("orderid", ""),
            "products": self.get_products_display(self.message.get("products", [])),
            "onlinerefund": self.message.get("onlinerefund", "0"),
            "walletrefund": self.message.get("walletrefund", "0"),
            "codamount": self.message.get("codamount", "0"),
            "reason": self.message.get("reason", ""),
            "url": self.generate_url(self.message.get("orderid", ""))
        }
    
    
    def get_products_display(self, products):
        if not products:
            return ""
        first_product = products[0]
        suffix = f" +{len(products) - 1}" if len(products) > 1 else ""
        if len(first_product) > 27:
            return first_product[:25] + "..." + suffix
        else:
            return first_product + suffix
    
    def format_template(self, template: str, values: dict) -> str:
        for key, val in values.items():
            template = template.replace(f"{{#{key}#}}", str(val))
        return template
    
    def generate_url(self, orderid):
        if orderid is None:
            return None
        track_orderid = base64.b64encode(str(orderid).encode('utf-8')).strip()
        track_orderid = track_orderid.decode('utf-8')
        return f"https://sastasundar.com/customers/dashboard/orderview/{track_orderid}"

