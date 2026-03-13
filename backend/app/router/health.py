from fastapi.routing import APIRouter

from app.core.success_response import success_response

health_router = APIRouter(prefix="/health")

@health_router.get("/live", tags=["健康检查"], summary="健康检查")
async def get_health_application_status():
    """健康检查-存活"""
    return success_response(
        message="health application status",
        data={
            "status": "ok"
        }
    )

@health_router.get("/ready", tags=["健康检查"], summary="健康检查")
async def get_health_readiness():
    """健康检查-就绪"""
    # 检查mysql、大模型api的连通性, 暂时先不完善
    return success_response(
        message="health readiness status",
        data={
            "status": "ok"
        }
    )

