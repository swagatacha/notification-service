from fastapi import APIRouter
from fastapi.responses import JSONResponse
from commons import RabbitMQConnection, RabbitMQConnectionPool, config, Mongo

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
        rabbitmq_conn = RabbitMQConnectionPool(pool_size=10) if config.RABBITMQ_CONNECTION_POOL else RabbitMQConnection()
        connection = rabbitmq_conn.get_connection()
        if isinstance(rabbitmq_conn, RabbitMQConnectionPool):
            rabbitmq_conn.release_connection(connection)
        else:
            connection.close()
        return True
    except Exception:
        return False

def is_mongodb_healthy():
    try:
        mongo = Mongo()
        mongo.db().command("ping")
        mongo.close()
        return True
    except Exception as e:
        return False