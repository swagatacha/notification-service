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
    "order_cancel",
    "user_registration"
]
rabbitmq_conn = RabbitMQConnectionPool(pool_size=10) if config.RABBITMQ_CONNECTION_POOL else RabbitMQConnection()

class RabbitMQSetup:
    def __init__(self):
            
        self.connection = rabbitmq_conn.get_connection()
        self.channel = self.connection.channel() if config.RABBITMQ_CONNECTION_POOL else self.connection.get_channel()
        self.EXCHANGE_NAME = config.EXCHANGE_NAME
        self.setup_rabbitmq()

    def declare_queue_with_ttl(self, queue_name, ttl_ms=30000):
        dlq_name = f"{config.EXCHANGE_NAME}.dlq"
        try:
            self.channel.queue_declare(queue=dlq_name, durable=True)
            args = {
                'x-message-ttl': ttl_ms 
            }

            args = {
                'x-message-ttl': ttl_ms,
                'x-dead-letter-exchange': '',  # default exchange
                'x-dead-letter-routing-key': dlq_name
            }

            self.channel.queue_declare(queue=queue_name, durable=True, arguments=args)
            logger.info(f"Declared queue {queue_name} with x-message-ttl={ttl_ms}")
        except Exception as e:
            logger.error(f"Error declaring queue {queue_name}: {traceback.format_exc()}")


    def setup_rabbitmq(self):
        try:
            self.channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='direct', durable=True)

            for queue in queues:
                self.declare_queue_with_ttl(queue, ttl_ms=30000)
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
