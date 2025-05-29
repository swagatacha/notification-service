from commons import RabbitMQConnection, RabbitMQConnectionPool, config, NotificationLogger
import traceback

log_clt = NotificationLogger()
logger = log_clt.get_logger()

# Queues and Routing Keys
queues = [
    "order_placed",
    "order_confirmed",
    "order_shipped",
    "order_delivered",
    "order_edit",
    "order_cancelled",
    "product_request",
    "reorder"
]
rabbitmq_conn = RabbitMQConnectionPool(pool_size=10) if config.RABBITMQ_CONNECTION_POOL else RabbitMQConnection()

class RabbitMQSetup:
    def __init__(self):
        logger.info(f"rabbitmq conection:{type(rabbitmq_conn)}") 
        self.connection = rabbitmq_conn.get_connection()
        self.channel = self.connection.channel()
        self.EXCHANGE_NAME = config.EXCHANGE_NAME
        self.setup_rabbitmq()

    def declare_queue_with_ttl(self, queue_name):
        dlq_name = f"{self.EXCHANGE_NAME}.dlq"
        try:
            self.channel.queue_declare(queue=dlq_name, durable=True)

            args = {
                'x-message-ttl': int(config.MSG_TTL_MS),
                'x-dead-letter-exchange': '',  # default exchange
                'x-dead-letter-routing-key': dlq_name
            }

            self.channel.queue_declare(queue=queue_name, durable=True, arguments=args)
            logger.info(f"Declared queue {queue_name} with x-message-ttl={config.MSG_TTL_MS}")
        except Exception as e:
            logger.error(f"Error declaring queue {queue_name}: {traceback.format_exc()}")


    def setup_rabbitmq(self):
        try:
            self.channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='direct', durable=True)

            for queue in queues:
                self.declare_queue_with_ttl(queue)
                self.channel.queue_bind(exchange=self.EXCHANGE_NAME, queue=queue, routing_key=queue)
                logger.info(f"Declared and bound queue: {queue}")

            if isinstance(rabbitmq_conn, RabbitMQConnectionPool):
                rabbitmq_conn.release_connection(self.connection)
            else:
                self.connection.close()

        except Exception as e:
            logger.error("RabbitMq queue binding failed: {}".format(traceback.format_exc()))

if __name__ == "__main__":
    RabbitMQSetup()
