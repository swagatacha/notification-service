import time
from functools import wraps
from commons import NotificationLogger

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

def retry(max_retries=3, delay=2, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                logger.info(f"retries:{retries} and max_retries:{max_retries}")
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"[Retry {retries}] {func.__name__} failed: {e}")
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries.")
                        raise e
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator
