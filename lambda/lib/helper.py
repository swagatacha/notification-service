import re
import os

def string_character_check(str, pattern):
    if re.search(pattern, str):
        return True
    else:
        return False

def user_type_validate(data: dict):
    allowed_user_type = {"C", "HB", "Admin"}
    if data['ActionBy'] is not None and data['ActionBy'] not in allowed_user_type:
        return False
    return True

def event_validate(data: dict):
    allowed_event_type = {"order_placed", "order_confirmed", "order_hold",
                       "order_delivered", "order_cancel", "order_edit", "order_shipped"}
    if data['Event'] is None:
        return False
    else:
        if data['Event'] not in allowed_event_type:
            return False
    return True
