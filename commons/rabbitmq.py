import pika
from commons import config
import time
import json
import requests
from requests.auth import HTTPBasicAuth

def get_connection(max_retries=5, delay=5):

    """Initialize RabbitMQ connection"""
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials
    )

    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[!] Connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(delay)

    raise Exception("RabbitMQ connection failed after retries")
    # connection = pika.BlockingConnection(
    #     pika.ConnectionParameters(host=config.RABBITMQ_HOST, port= config.RABBITMQ_PORT, credentials=credentials)
    # )

    return connection

def get_bound_queues():
    RABBITMQ_API = f'http://{config.RABBITMQ_HOST}:{config.RABBITMQ_MANAGEMENT_PORT}/api/bindings/%2F'
    #RABBITMQ_API = f'http://localhost:{config.RABBITMQ_MANAGEMENT_PORT}/api/bindings/%2F'
    print(RABBITMQ_API)
    response = requests.get(RABBITMQ_API, auth=HTTPBasicAuth(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD))
    response.raise_for_status()
    print(response)
    bindings = response.json()
    print(bindings)
    return [b["destination"] for b in bindings if b["source"] == "notification_events" and b["destination_type"] == "queue"]
    # return {
    #     b['destination']
    #     for b in bindings
    #     if b['destination_type'] == 'queue'
    # }


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