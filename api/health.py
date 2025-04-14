from fastapi import APIRouter
from fastapi.responses import JSONResponse
from commons import rabbitmq

router = APIRouter()

@router.get("/healthz")
def liveness_probe():
    return {"status": "alive"}

@router.get("/readyz")
def readiness_probe():
    if is_rabbitmq_healthy():
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not ready"})

def is_rabbitmq_healthy():
    try:
        connection = rabbitmq.get_connection()
        connection.close()
        return True
    except Exception:
        return False
