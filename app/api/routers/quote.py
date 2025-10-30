import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import User
from app.db.session import get_db
from app.deps import get_current_user_optional
from app.schemas.quote import QuoteRequest
from app.services.calculator_service import compute_quote
from app.services.settings_service import create_settings_snapshot
from app.utils.exceptions import handle_common_exceptions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["报价"])


@router.post("")
@handle_common_exceptions(
    file_not_found_msg="图片文件未找到",
    value_error_msg="报价计算参数错误",
    general_error_msg="计算报价时发生内部错误",
)
async def calculate_quote(
    quote_req: QuoteRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    """计算报价"""

    # 执行计算
    result = compute_quote(
        db=db,
        length=quote_req.length,
        width=quote_req.width,
        thickness=quote_req.thickness,
        color_count=quote_req.color_count,
        area_ratio=quote_req.area_ratio,
        order_quantity=quote_req.order_quantity,
        worker_type=quote_req.worker_type,
        debug=quote_req.debug,
    )

    # 附加设置快照，便于历史可追溯
    try:
        settings_snapshot = create_settings_snapshot(db)
        result["settings_snapshot"] = settings_snapshot
    except Exception as e:
        logger.error(f"保存设置快照失败: {e}")
        # 不影响报价结果的返回

    # 保存历史记录（如果用户已登录）
    history_id = None
    if current_user:
        try:
            history = crud.create_history(
                db=db,
                user_id=current_user.id,
                request_payload=quote_req.model_dump(),
                result_payload=result,
                worker_type=quote_req.worker_type,
                unit_price=result.get("产品单价", 0.0),
                total_price=result.get("订单货款总额", 0.0),
            )
            history_id = history.id
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            # 不影响报价结果的返回

    # 将history_id添加到结果中，便于前端收藏
    if history_id:
        result["history_id"] = history_id

    return result
