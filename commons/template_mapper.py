import base64
from commons import config, NotificationLogger
from .enums import PaymentTypeMap, ActionByMap, map_enum_value

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class TemplateValueMapper:

    def __init__(self, message: dict):
        self.message = message

    def get_values(self) -> dict:
        return {
            "pname": self.message.get("fname", "Customer"),
            "orderamount": self.message.get("orderamount", 0),
            "orderid": self.message.get("orderid", ""),
            "products": self.get_products_display(self.message.get("products", [])),
            "onlinerefund": self.message.get("onlinerefund", "0"),
            "walletrefund": self.message.get("walletrefund", "0"),
            "codamount": self.message.get("codamount", "0"),
            "reason": self.message.get("reason", ""),
            "url": self.generate_url(self.message.get("orderid", "")),
            "discountpercent": self.message.get("discountpercent", ""),
            "discountamount": self.message.get("discountamount", ""),
            "couponcode": self.message.get("couponcode", ""),
            "customercare": config.CUSTOMER_CARE
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
    
    @staticmethod
    def formatted_event_id(client_request_id:str) -> str:
        parts = client_request_id.split("_")
        if len(parts) == 2:
            return client_request_id
        
        event_name = "_".join(parts[:2])
        mapped_parts = [event_name]

        if len(parts) > 2:
            mapped_parts.append(map_enum_value(PaymentTypeMap, str(parts[2])).lower())
        if len(parts) > 3:
            mapped_parts.append(map_enum_value(ActionByMap, str(parts[3])).lower())

        return "_".join(mapped_parts)
    
    @staticmethod
    def formatted_payment_type(payment_type:str) -> str:

        if payment_type is None or len(payment_type) == 0:
            return payment_type  

        return map_enum_value(PaymentTypeMap, str(payment_type)).lower()
    
    @staticmethod
    def formatted_action_by(action_by:str) -> str:
        if action_by is None or len(action_by) == 0:
            return action_by  

        return map_enum_value(ActionByMap, str(action_by)).lower()
        

