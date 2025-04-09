import pika
from commons import config
import time
import json

def get_connection():

    """Initialize RabbitMQ connection"""
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST, port= config.RABBITMQ_PORT, credentials=credentials)
    )

    return connection

def start_consumer(queue_name, callback):
    while True:
        try:
            connection = get_connection()
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            def wrapper(ch, method, properties, body):
                message = json.loads(body)
                callback(message)

            channel.basic_consume(queue=queue_name, on_message_callback=wrapper, auto_ack=True)

            print(f"[*] Waiting for messages on {queue_name}...")
            channel.start_consuming()
        except Exception as e:
            print(f"[!] Consumer for {queue_name} crashed: {e}")
            time.sleep(5)  # backoff and retry