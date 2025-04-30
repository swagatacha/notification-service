import re
import os

def string_character_check(str, pattern):
    if re.search(pattern, str):
        return True
    else:
        return False

def user_type_validate(data: dict) -> bool:
    allowed_user_type = {"c", "hb", "admin"}
    action_by = data.get('ActionBy','')
    if action_by is not None and action_by.lower() not in allowed_user_type:
        return False
    return True

def order_type_validate(data:dict) -> bool:
    allowed_order_type = {"otc", "med"}
    order_type = data.get('OrderType','')
    if order_type is not None and order_type.lower() not in allowed_order_type:
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
    payment_type = data.get('PaymentType','')
    if payment_type:
        normalized_input = frozenset(part.strip().lower() for part in payment_type.replace("+", " ").split())  
        if normalized_input not in allowed_payment_type_combos:
            return False
    return True

def event_validate(data: dict) -> bool:
    allowed_event_type = {"order_placed", "order_confirmed", "order_hold",
                       "order_delivered", "order_cancelled", "order_edit", "order_shipped"}
    event = data.get('Event','')
    if event is None:
        return False
    else:
        if event.lower() not in allowed_event_type:
            return False
    return True
