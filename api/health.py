from fastapi import APIRouter
from fastapi.responses import JSONResponse
from commons import rabbitmq, mongodb

router = APIRouter()

@router.get("/healthz")
def liveness_probe():
    return {"status": "alive"}

@router.get("/readyz")
def readiness_probe():
    rabbitmq_ok = is_rabbitmq_healthy()
    mongodb_ok = is_mongodb_healthy()

    if rabbitmq_ok and mongodb_ok:
        return {"status": "ready"}
    
    return JSONResponse(
        status_code=503,
        content={
            "status": "not ready",
            "rabbitmq": rabbitmq_ok,
            "mongodb": mongodb_ok
        }
    )

def is_rabbitmq_healthy():
    try:
        connection = rabbitmq.get_connection()
        connection.close()
        return True
    except Exception:
        return False

def is_mongodb_healthy():
    try:
        mongo = mongodb.Mongo()
        mongo.db().command("ping")
        mongo.close()
        return True
    except Exception as e:
        return False