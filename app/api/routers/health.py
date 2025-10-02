from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


