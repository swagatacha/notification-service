from datetime import datetime
import json
import pika
from dal.sql.sql_dal import NoSQLDal
from commons import RabbitMQConnection, RabbitMQConnectionPool, config, NotificationLogger

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

rabbitmq_conn = RabbitMQConnectionPool(pool_size=10) if config.RABBITMQ_CONNECTION_POOL else RabbitMQConnection()

class DlqProcessor:
    def __init__(self):
        self.connection = rabbitmq_conn.get_connection()
        self.channel = self.connection.channel()
        self.__dal = NoSQLDal()

    def requeue_from_dlq(self):
        channel = self.channel

        dlq_name = f"{config.EXCHANGE_NAME}.dlq"
        requeue_exchange = config.EXCHANGE_NAME
        max_retries = config.REQUEUE_MAX_RETRIES

        def callback(ch, method, properties, body):
            try:
                # Extract retry count from headers, default to 0
                retry_headers = dict(properties.headers or {})
                retry_count = int(retry_headers.get("x-retry-count", 0))

                # If the message has been retried already, drop it (or send to a permanent failure queue)
                if retry_count >= max_retries:
                    logger.info(f"Message already retried. Dropping message: {body}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    message = json.loads(body)
                    data={
                        "mobileNo": message.get("mobileno"),
                        "event": message.get("message_key"),
                        "orderId":message.get("orderid",''),
                        "response": f"Message already retried. Dropping message: {body}",
                        "createdAt": datetime.utcnow()
                    }
                    self.__dal.save_log(data)
                    return  # Drop the message
                
                # Increment retry count and add to headers
                retry_headers["x-retry-count"] = retry_count + 1
                retry_headers.setdefault("x-original-routing-key", method.routing_key.replace('.dlq', ''))

                updated_properties = pika.BasicProperties(
                    headers=retry_headers,
                    content_type=properties.content_type,
                    content_encoding=properties.content_encoding,
                    delivery_mode=properties.delivery_mode,
                    priority=properties.priority,
                    correlation_id=properties.correlation_id,
                    reply_to=properties.reply_to,
                    expiration=properties.expiration,
                    message_id=properties.message_id,
                    timestamp=properties.timestamp,
                    type=properties.type,
                    user_id=properties.user_id,
                    app_id=properties.app_id
                )

                original_routing_key = retry_headers["x-original-routing-key"]

                channel.basic_publish(
                    exchange=requeue_exchange,
                    routing_key=original_routing_key,
                    body=body,
                    properties=updated_properties
                )

                logger.info(f"Requeued message from DLQ to {original_routing_key}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"Failed to requeue message from DLQ: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_consume(
            queue=dlq_name,
            on_message_callback=callback,
            auto_ack=False
        )

        logger.info(f"Starting DLQ requeue consumer on {dlq_name}")
        channel.start_consuming()

    