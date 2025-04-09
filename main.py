from fastapi import FastAPI
from pkgutil import walk_packages
from importlib import import_module
import threading
import uvicorn
import api
import rabbitmq_queue_setup
from consumers import (
    order_placed, order_confirmed, order_shipped,
    order_delivered, order_edit, user_registration
)
from biz.notification_processor import process_message

consumers_list = [
    ("order_placed", order_placed),
    ("order_confirmed", order_confirmed),
    ("order_shipped", order_shipped),
    ("order_delivered", order_delivered),
    ("order_edit", order_edit),
    ("user_registration", user_registration)
]

app = FastAPI()

for importer, package_name, ispkg in walk_packages(path=api.__path__):
    if ispkg:
        views = import_module('.views', api.__name__ + "." + package_name)
        app.include_router(views.router)

def start_all_consumers():
    # threading.Thread(target=order_placed.start_consumer, daemon=True).start()
    # threading.Thread(target=order_confirmed.start_consumer, daemon=True).start()
    # threading.Thread(target=order_shipped.start_consumer, daemon=True).start()
    # threading.Thread(target=order_delivered.start_consumer, daemon=True).start()
    # threading.Thread(target=order_edit.start_consumer, daemon=True).start()
    # threading.Thread(target=user_registration.start_consumer, daemon=True).start()
    for queue_name, consumer_module in consumers_list:
        threading.Thread(
            target=consumer_module.start_consumer,
            args=(queue_name, process_message),
            daemon=True
        ).start()

@app.on_event("startup")
def startup_event():
    print("Setting up Queues...")
    rabbitmq_queue_setup.RabbitMQSetup()

    print("Starting Consumers...")
    start_all_consumers()


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down gracefully...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
