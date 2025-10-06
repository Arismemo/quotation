from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查接口"""
    return {"status": "ok"}
