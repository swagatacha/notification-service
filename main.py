from fastapi import FastAPI
from pkgutil import walk_packages
from importlib import import_module
import threading
import uvicorn
import api
from api import health
#import rabbitmq_queue_setup
from consumers import (
    order_placed, order_confirmed, order_shipped,
    order_delivered, order_edit, user_registration
)
from commons import rabbitmq
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

app.include_router(health.router)

for importer, package_name, ispkg in walk_packages(path=api.__path__):
    if ispkg:
        views = import_module('.views', api.__name__ + "." + package_name)
        app.include_router(views.router)

def start_all_consumers(): 
    print("Fetching dynamically bound queues...")
    queues = rabbitmq.get_bound_queues()
    print(f"Queues detected: {queues}")

    for queue_name in queues:
        print(f"Launching consumer thread for: {queue_name}")
        threading.Thread(
            target=rabbitmq.start_consumer,
            args=(queue_name, process_message),
            daemon=True
        ).start()

@app.on_event("startup")
def startup_event():
    print("Starting Consumers...")
    start_all_consumers()


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down gracefully...")


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)
