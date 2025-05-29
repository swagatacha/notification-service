import re
import os

def string_character_check(str, pattern):
    if re.search(pattern, str):
        return True
    else:
        return False

def user_type_validate(data: dict) -> bool:
    allowed_user_type = {"c", "hb", "admin"}
    action_by = data.get('actionby','')
    if action_by is not None and action_by.lower() not in allowed_user_type:
        return False
    return True

def payment_type_validate(data:dict) -> bool:
    allowed_payment_type_combos = {
        frozenset(["cod"]),
        frozenset(["online"]),
        frozenset(["wallet"]),
        frozenset(["online", "wallet"]),
        frozenset(["cod", "wallet"])
    }
    payment_type = data.get('paymenttype','')
    if payment_type:
        normalized_input = frozenset(part.strip().lower() for part in payment_type.replace("+", " ").split())  
        if normalized_input not in allowed_payment_type_combos:
            return False
    return True

def event_validate(data: dict) -> bool:
    allowed_event_type = {"order_placed", "order_confirmed", "order_hold",
                       "order_delivered", "order_cancelled", "order_edit", "order_shipped","product_request"}
    event = data.get('event','')
    if event is None:
        return False
    else:
        if event.lower() not in allowed_event_type:
            return False
    return True
