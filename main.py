from fastapi import FastAPI
from pkgutil import walk_packages
from importlib import import_module
import threading
import uvicorn
import api
from api import health
from commons import config, RabbitMQConnection, RabbitMQConnectionPool
from biz.notification_processor import process_message, logger
from biz.dlq_processor import DlqProcessor

app = FastAPI()

app.include_router(health.router)
rabbitmq_conn = RabbitMQConnectionPool(pool_size=10) if config.RABBITMQ_CONNECTION_POOL else RabbitMQConnection()

for importer, package_name, ispkg in walk_packages(path=api.__path__):
    if ispkg:
        views = import_module('.views', api.__name__ + "." + package_name)
        app.include_router(views.router)


def start_all_consumers(): 
    queues = rabbitmq_conn.get_bound_queues()

    for queue_name in queues:
        logger.info(f"Launching consumer thread for: {queue_name}")
        threading.Thread(
            target=rabbitmq_conn.start_consumer,
            args=(queue_name, process_message),
            daemon=True
        ).start()

    # Additionally consume DLQ
    dlq_name = f"{config.EXCHANGE_NAME}.dlq"
    logger.info(f"Submitting DLQ requeue task for: {dlq_name}")
    threading.Thread(
        target=DlqProcessor().requeue_from_dlq,
        daemon=True
    ).start()

@app.on_event("startup")
def startup_event():
    start_all_consumers()

@app.on_event("shutdown")
def shutdown_event():
    if hasattr(rabbitmq_conn, "close"):
        try:
            rabbitmq_conn.close()
            logger.info("RabbitMQ connection closed successfully.")
        except Exception as e:
            logger.warning(f"Failed to close RabbitMQ connection: {e}")