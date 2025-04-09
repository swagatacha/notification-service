from commons.rabbitmq import start_consumer
from biz.notification_processor import process_message

QUEUE_NAME = "order_placed"

if __name__ == "__main__":
    print("order_placed consumer running")
    start_consumer(QUEUE_NAME, process_message)
