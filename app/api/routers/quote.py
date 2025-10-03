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
        
        # 附加设置快照，便于历史可追溯
        try:
            app_settings = crud.get_app_settings(db)
            worker_profiles = crud.get_worker_profiles(db)
            settings_snapshot = {
                "settings": {
                    "profit_margin": app_settings.profit_margin,
                    "waste_rate": app_settings.waste_rate,
                    "material_density": app_settings.material_density,
                    "material_price_per_gram": app_settings.material_price_per_gram,
                    "mold_edge_length": app_settings.mold_edge_length,
                    "mold_spacing": app_settings.mold_spacing,
                    "base_molds_per_shift": app_settings.base_molds_per_shift,
                    "working_days_per_month": app_settings.working_days_per_month,
                    "shifts_per_day": app_settings.shifts_per_day,
                    "needles_per_machine": app_settings.needles_per_machine,
                    "setup_fee_per_color": app_settings.setup_fee_per_color,
                    "base_setup_fee": app_settings.base_setup_fee,
                    "coloring_fee_per_color_per_shift": app_settings.coloring_fee_per_color_per_shift,
                    "other_salary_per_cell_shift": app_settings.other_salary_per_cell_shift,
                    "rent_per_cell_shift": app_settings.rent_per_cell_shift,
                    "electricity_fee_per_cell_shift": app_settings.electricity_fee_per_cell_shift,
                },
                "worker_profiles": [
                    {
                        "name": wp.name,
                        "monthly_salary": wp.monthly_salary,
                        "machines_operated": wp.machines_operated,
                    } for wp in worker_profiles
                ]
            }
            # 将快照随结果返回（前端不展示也无妨），并随历史保存
            result["settings_snapshot"] = settings_snapshot
        except Exception as e:
            logger.error(f"附加设置快照失败: {e}")
        
        # 如果用户已登录，自动写入历史
        history_id = None
        if current_user:
            try:
                request_payload = quote_req.model_dump()
                history_record = crud.create_history(
                    db=db,
                    user_id=current_user.id,
                    request_payload=request_payload,
                    result_payload=result,
                    worker_type=quote_req.worker_type,
                    unit_price=result.get("产品单价", 0),
                    total_price=result.get("订单货款总额", 0)
                )
                history_id = history_record.id
                logger.info(f"用户 {current_user.username} 的报价已保存到历史，ID: {history_id}")
            except Exception as e:
                logger.error(f"保存历史记录失败: {e}")
                # 不影响报价结果的返回
        
        # 将history_id添加到结果中，便于前端收藏
        if history_id:
            result["history_id"] = history_id
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"计算报价时发生错误: {e}")
        raise HTTPException(status_code=500, detail="计算报价时发生内部错误")


