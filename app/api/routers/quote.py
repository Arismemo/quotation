from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.quote import QuoteRequest
from app.services.calculator_service import compute_quote
from app.deps import get_current_user_optional
from app.db.models import User
from app.db import crud
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quote", tags=["报价"])


@router.post("")
async def calculate_quote(
    quote_req: QuoteRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """计算报价"""
    
    try:
        # 执行计算
        result = compute_quote(
            db=db,
            length=quote_req.length,
            width=quote_req.width,
            thickness=quote_req.thickness,
            color_count=quote_req.color_count,
            area_ratio=quote_req.area_ratio,
            difficulty_factor=quote_req.difficulty_factor,
            order_quantity=quote_req.order_quantity,
            worker_type=quote_req.worker_type,
            debug=quote_req.debug
        )
        
        # 如果用户已登录，自动写入历史
        if current_user:
            try:
                request_payload = quote_req.model_dump()
                crud.create_history(
                    db=db,
                    user_id=current_user.id,
                    request_payload=request_payload,
                    result_payload=result,
                    worker_type=quote_req.worker_type,
                    unit_price=result.get("产品单价", 0),
                    total_price=result.get("订单货款总额", 0)
                )
                logger.info(f"用户 {current_user.username} 的报价已保存到历史")
            except Exception as e:
                logger.error(f"保存历史记录失败: {e}")
                # 不影响报价结果的返回
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"计算报价时发生错误: {e}")
        raise HTTPException(status_code=500, detail="计算报价时发生内部错误")


