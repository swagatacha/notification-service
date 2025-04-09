from commons.rabbitmq import start_consumer
from biz.notification_processor import process_message

QUEUE_NAME = "ordorder_delivereder_confirmed"

if __name__ == "__main__":
    print("order_delivered consumer running")
    start_consumer(QUEUE_NAME, process_message)
