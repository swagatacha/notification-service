from commons import RedisClient
from biz.notification_processor import buffer_queue_fallback

def scan_and_process():
    redis_client = RedisClient().get_client()
    pending_key = "pending_notifications_all"

    # Get all fields (keys) from the hash
    keys = redis_client.hkeys(pending_key)

    for full_key in keys:
        try:
            # Redis returns keys as bytes, decode if needed
            full_key_str = full_key.decode() if isinstance(full_key, bytes) else full_key
            order_id = full_key_str.split(":")[0]

            print(f"Processing order {order_id} from key {full_key_str}")
            buffer_queue_fallback(redis_client, order_id, pending_key)
        except Exception as e:
            print(f"Error processing key {full_key}: {e}")

if __name__ == "__main__":
    scan_and_process()
