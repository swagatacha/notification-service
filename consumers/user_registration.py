from commons.rabbitmq import start_consumer
from biz.notification_processor import process_message

QUEUE_NAME = "user_registration"

if __name__ == "__main__":
    print("user_registration consumer running")
    start_consumer(QUEUE_NAME, process_message)
