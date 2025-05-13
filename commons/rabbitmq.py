import pika
import threading
from queue import Queue
from commons import config, NotificationLogger, Singleton
import time
import json
import requests
from requests.auth import HTTPBasicAuth

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class RabbitMQConnection(metaclass=Singleton):
    def __init__(self):
        self.connection = self.create_connection()

    def create_connection(self):

        """Initialize RabbitMQ connection"""
        credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            credentials=credentials
        )
        return pika.BlockingConnection(parameters)
    
    def get_connection(self):
        if self.connection.is_open:
            return self.connection
        self.connection = self.create_connection()
        return self.connection

    def get_channel(self):
        if self.connection.is_closed:
            self.connection = self.get_connection()
        return self.connection.channel()
    
    def get_bound_queues(self):
        RABBITMQ_API = f'http://{config.RABBITMQ_HOST}:{config.RABBITMQ_MANAGEMENT_PORT}/api/bindings/%2F'
        response = requests.get(RABBITMQ_API, auth=HTTPBasicAuth(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD))
        response.raise_for_status()
        bindings = response.json()
        return [b["destination"] for b in bindings if b["source"] == f"{config.EXCHANGE_NAME}" and b["destination_type"] == "queue"]
    
    def declare_managed_queue(self, channel, queue_name):
        dlq_name = f"{config.EXCHANGE_NAME}.dlq"

        dlq_name = f"{config.EXCHANGE_NAME}.dlq"

        #channel.queue_declare(queue=dlq_name, durable=True)
        try:
            channel.queue_declare(queue=dlq_name, durable=True, passive=True)
            logger.info(f"DLQ '{dlq_name}' already exists.")
        except pika.exceptions.ChannelClosedByBroker:
            logger.warning(f"DLQ '{dlq_name}' not found. Declaring it.")
            channel = self.get_connection().channel()
            channel.queue_declare(queue=dlq_name, durable=True)

        try:
            channel.queue_declare(queue=queue_name, durable=True, passive=True)
            logger.info(f"Queue '{queue_name}' already exists.")
        except pika.exceptions.ChannelClosedByBroker:
            logger.warning(f"Queue '{queue_name}' not found. Declaring it with arguments.")
            channel = self.get_connection().channel()
            args = {
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': dlq_name,
                'x-message-ttl': int(config.MSG_TTL_MS)
            }
            channel.queue_declare(queue=queue_name, durable=True, arguments=args)
            logger.info(f"Declared queue '{queue_name}' with DLQ '{dlq_name}'")

    def start_consumer(self, queue_name, callback, max_attempts=5):
        attempt = 0
        backoff = 2

        while attempt < max_attempts:
            connection = None
            channel = None
            try:
                connection = self.get_connection()
                channel = connection.channel()
                self.declare_managed_queue(channel, queue_name)

                def wrapper(ch, method, properties, body):
                    try:
                        message = json.loads(body)
                        callback(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=queue_name, on_message_callback=wrapper)

                logger.info(f"Waiting for messages on {queue_name}...")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Consumer for {queue_name} crashed: {e}")
                attempt += 1
                wait_time = min(backoff * (2 ** attempt), 60)
                
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            finally:
                if channel:
                    try:
                        channel.close()
                    except Exception as close_err:
                        logger.warning(f"Error closing channel: {close_err}")
                if connection:
                    try:
                        connection.close()
                    except Exception as close_err:
                        logger.warning(f"Error closing connection: {close_err}")

        logger.error(f"Max retry attempts reached for {queue_name}. Consumer exiting.")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

class RabbitMQConnectionPool:
    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        for _ in range(pool_size):
            self.pool.put(self.create_connection())

    def create_connection(self):
        credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            credentials=credentials
        )
        return pika.BlockingConnection(parameters)

    def get_connection(self):
        with self.lock:
            while not self.pool.empty():
                conn = self.pool.get()
                if conn.is_open:
                    return conn
                else:
                    logger.warning("Skipping closed connection from pool.")
        return self.create_connection()

    def release_connection(self, connection):
        with self.lock:
            if connection and connection.is_open and not self.pool.full():
                self.pool.put(connection)
            else:
                try:
                    connection.close()
                except Exception as e:
                    logger.warning(f"Failed to close connection: {e}")

    def get_bound_queues(self):
        RABBITMQ_API = f'http://{config.RABBITMQ_HOST}:{config.RABBITMQ_MANAGEMENT_PORT}/api/bindings/%2F'
        response = requests.get(RABBITMQ_API, auth=HTTPBasicAuth(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD))
        response.raise_for_status()
        bindings = response.json()
        return [b["destination"] for b in bindings if b["source"] == f"{config.EXCHANGE_NAME}" and b["destination_type"] == "queue"]

    def declare_managed_queue(self, channel, queue_name):
        dlq_name = f"{config.EXCHANGE_NAME}.dlq"

        #channel.queue_declare(queue=dlq_name, durable=True)
        try:
            channel.queue_declare(queue=dlq_name, durable=True, passive=True)
            logger.info(f"DLQ '{dlq_name}' already exists.")
        except pika.exceptions.ChannelClosedByBroker:
            logger.warning(f"DLQ '{dlq_name}' not found. Declaring it.")
            channel = self.get_connection().channel()
            channel.queue_declare(queue=dlq_name, durable=True)

        try:
            channel.queue_declare(queue=queue_name, durable=True, passive=True)
            logger.info(f"Queue '{queue_name}' already exists.")
        except pika.exceptions.ChannelClosedByBroker:
            logger.warning(f"Queue '{queue_name}' not found. Declaring it with arguments.")
            channel = self.get_connection().channel()
            args = {
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': dlq_name,
                'x-message-ttl': int(config.MSG_TTL_MS)
            }
            channel.queue_declare(queue=queue_name, durable=True, arguments=args)
            logger.info(f"Declared queue '{queue_name}' with DLQ '{dlq_name}'")
    
    def start_consumer(self, queue_name, callback, max_attempts=5):
        attempt = 0
        backoff = 2

        while attempt < max_attempts:
            connection = None
            channel = None
            try:
                connection = self.get_connection()
                channel = connection.channel()
                self.declare_managed_queue(channel, queue_name)

                def wrapper(ch, method, properties, body):
                    try:
                        message = json.loads(body)
                        callback(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=queue_name, on_message_callback=wrapper)

                logger.info(f"Waiting for messages on {queue_name}...")
                channel.start_consuming()

            except Exception as e:
                logger.error(f"Consumer for {queue_name} crashed: {e}")
                attempt += 1
                wait_time = min(backoff * (2 ** attempt), 60)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            finally:
                if channel:
                    try:
                        channel.close()
                    except Exception as close_err:
                        logger.warning(f"Error closing channel: {close_err}")
                if connection:
                    try:
                        self.release_connection(connection)
                    except Exception as close_err:
                        logger.warning(f"Error closing connection: {close_err}")

        logger.error(f"Max retry attempts reached for {queue_name}. Exiting consumer thread.")

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

