import json
from base64 import b64encode, b64decode


def encode(data: dict):
    return b64encode(json.dumps(data).encode("ascii"))


def decode(data: bytes):
    return json.loads(b64decode(data))
