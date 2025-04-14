import pika
from commons import rabbitmq
from commons import config

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

class RabbitMQSetup:
    def __init__(self):
        
        self.connection = rabbitmq.get_connection()
        self.channel = self.connection.channel()
        self.EXCHANGE_NAME = config.EXCHANGE_NAME
        self.setup_rabbitmq()

    def setup_rabbitmq(self):
        """Creates queues and binds them to the exchange."""
        # Declare Exchange (Direct Type)
        self.channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='direct', durable=True)

        # Declare Queues and Bind to Exchange
        for queue in queues:
            self.channel.queue_declare(queue=queue, durable=True)
            self.channel.queue_bind(exchange=self.EXCHANGE_NAME, queue=queue, routing_key=queue)
            print(f"Queue '{queue}' bound to exchange '{self.EXCHANGE_NAME}' with routing key '{queue}'")

        # Close Connection
        self.connection.close()
        print("RabbitMQ setup completed.")

if __name__ == "__main__":
    RabbitMQSetup()
