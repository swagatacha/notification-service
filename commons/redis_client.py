import redis
from commons import config
from commons.singleton import Singleton

class RedisClient(metaclass=Singleton):
    def __init__(self):
        self.client = redis.Redis(
            host=config.redis['host'],
            port=config.redis['port'],
            decode_responses=True
        )

    def get_client(self):
        return self.client
