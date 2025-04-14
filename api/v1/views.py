from fastapi import APIRouter
from commons import rabbitmq

router = APIRouter(
    prefix="/api/v1"
)

@router.get("/project-info")
def project_info():
    return {
        "service": "notification_service",
        "version": "v1"
    }
