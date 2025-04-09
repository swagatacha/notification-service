from fastapi import APIRouter
from commons import rabbitmq

router = APIRouter(
    prefix="/api/v1"
)

@router.get("/live")
def liveness_probe():
    return {"status": "alive"}

@router.get("/ready")
def readiness_probe():
    # Check RabbitMQ Connection
    if is_rabbitmq_healthy():
        return {"status": "ready"}
    return {"status": "not ready"}, 503

def is_rabbitmq_healthy():
    try:
        connection = rabbitmq.get_connection()
        connection.close()
        return True
    except Exception:
        return False
