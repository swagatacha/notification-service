from enum import Enum

class PaymentTypeMap(Enum):
    cod = (1, "COD")
    online = (2, "Online")
    wallet = (3, "Wallet")
    onlinewallet = (4, "Online+Wallet")
    codwallet = (5, "Cod+Wallet")

    def __init__(self, key, label):
        self.key = key
        self.label = label

class ActionByMap(Enum): 
    C = ("C", "Customer")
    A = ("A", "Admin")
    B = ("B", "HB")

    def __init__(self, key, label):
        self.key = key
        self.label = label

class OrderTypeMap(Enum):
    O = ("O", "Otc")
    M = ("M", "Med")

    def __init__(self, key, label):
        self.key = key
        self.label = label

def map_enum_value(enum_cls, key: str, default=None) -> str:
    try:
        return next(e.label for e in enum_cls if str(e.key).lower() == key.lower())
    except StopIteration:
        return default if default is not None else key