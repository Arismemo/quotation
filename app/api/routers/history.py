import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import User
from app.db.session import get_db
from app.deps import get_current_user
from app.schemas.history import HistoryItemResponse

router = APIRouter(tags=["报价历史"])


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    history_ids: list[int]


@router.get("", response_model=list[HistoryItemResponse])
async def get_histories(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    from_dt: Optional[str] = Query(None, description="起始时间，ISO字符串"),
    to_dt: Optional[str] = Query(None, description="结束时间，ISO字符串"),
    worker_type: Optional[str] = Query(None, description="工人类型过滤"),
    min_unit: Optional[float] = Query(None, description="最小单价"),
    max_unit: Optional[float] = Query(None, description="最大单价"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的报价历史列表（支持筛选）"""
    # 基础查询
    q = db.query(crud.QuotationHistory).filter(
        crud.QuotationHistory.user_id == current_user.id
    )

    # 时间范围
    def parse_iso(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    start = parse_iso(from_dt)
    end = parse_iso(to_dt)
    if start:
        q = q.filter(crud.QuotationHistory.computed_at >= start)
    if end:
        q = q.filter(crud.QuotationHistory.computed_at <= end)

    # 其他筛选
    if worker_type:
        q = q.filter(crud.QuotationHistory.worker_type == worker_type)
    if min_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price >= min_unit)
    if max_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price <= max_unit)

    histories = (
        q.order_by(crud.QuotationHistory.computed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 检查每条历史是否已收藏
    result = []
    for history in histories:
        is_favorited = crud.check_favorite_exists(db, current_user.id, history.id)
        history_dict = HistoryItemResponse.model_validate(history).model_dump()
        history_dict["is_favorited"] = is_favorited
        result.append(history_dict)

    return result


@router.get("/{history_id}", response_model=HistoryItemResponse)
async def get_history_detail(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单条历史记录详情"""
    history = crud.get_history_by_id(db, history_id, current_user.id)
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权访问")

    is_favorited = crud.check_favorite_exists(db, current_user.id, history.id)
    history_dict = HistoryItemResponse.model_validate(history).model_dump()
    history_dict["is_favorited"] = is_favorited

    return history_dict


@router.delete("/{history_id}")
async def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除历史记录"""
    success = crud.delete_history(db, history_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权删除")

    return {"message": "历史记录已删除"}


@router.post("/batch-delete")
async def batch_delete_histories(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除历史记录"""
    if not request.history_ids:
        raise HTTPException(status_code=400, detail="请提供要删除的历史记录ID")
    
    deleted_count = 0
    failed_ids = []
    
    for history_id in request.history_ids:
        success = crud.delete_history(db, history_id, current_user.id)
        if success:
            deleted_count += 1
        else:
            failed_ids.append(history_id)
    
    return {
        "deleted_count": deleted_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids,
        "message": f"成功删除 {deleted_count} 条记录"
    }


@router.get("/export/csv")
async def export_histories_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    from_dt: Optional[str] = Query(None),
    to_dt: Optional[str] = Query(None),
    worker_type: Optional[str] = Query(None),
    min_unit: Optional[float] = Query(None),
    max_unit: Optional[float] = Query(None),
):
    """导出历史为CSV"""
    q = db.query(crud.QuotationHistory).filter(
        crud.QuotationHistory.user_id == current_user.id
    )

    def parse_iso(s: Optional[str]):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    start = parse_iso(from_dt)
    end = parse_iso(to_dt)
    if start:
        q = q.filter(crud.QuotationHistory.computed_at >= start)
    if end:
        q = q.filter(crud.QuotationHistory.computed_at <= end)
    if worker_type:
        q = q.filter(crud.QuotationHistory.worker_type == worker_type)
    if min_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price >= min_unit)
    if max_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price <= max_unit)
    rows = q.order_by(crud.QuotationHistory.computed_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["时间", "工人类型", "单价", "数量", "总额"])
    for h in rows:
        qty = (
            h.request_payload.get("order_quantity")
            if isinstance(h.request_payload, dict)
            else ""
        )
        writer.writerow(
            [
                h.computed_at.isoformat(sep=" ", timespec="seconds"),
                h.worker_type,
                h.unit_price,
                qty,
                h.total_price,
            ]
        )
    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=quotation_history.csv"},
    )


@router.get("/export/excel")
async def export_histories_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    from_dt: Optional[str] = Query(None),
    to_dt: Optional[str] = Query(None),
    worker_type: Optional[str] = Query(None),
    min_unit: Optional[float] = Query(None),
    max_unit: Optional[float] = Query(None),
):
    """导出历史为Excel（使用openpyxl）"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Excel导出功能需要安装 openpyxl: pip install openpyxl"
        )
    
    q = db.query(crud.QuotationHistory).filter(
        crud.QuotationHistory.user_id == current_user.id
    )

    def parse_iso(s: Optional[str]):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    start = parse_iso(from_dt)
    end = parse_iso(to_dt)
    if start:
        q = q.filter(crud.QuotationHistory.computed_at >= start)
    if end:
        q = q.filter(crud.QuotationHistory.computed_at <= end)
    if worker_type:
        q = q.filter(crud.QuotationHistory.worker_type == worker_type)
    if min_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price >= min_unit)
    if max_unit is not None:
        q = q.filter(crud.QuotationHistory.unit_price <= max_unit)
    
    rows = q.order_by(crud.QuotationHistory.computed_at.desc()).all()
    
    # 创建Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "报价历史"
    
    # 设置表头
    headers = ["时间", "工人类型", "单价(元)", "订单数量", "总价(元)", "长(cm)", "宽(cm)", "厚(cm)", "颜色数", "面积比例"]
    ws.append(headers)
    
    # 设置表头样式
    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # 填充数据
    for h in rows:
        request_data = h.request_payload if isinstance(h.request_payload, dict) else {}
        ws.append([
            h.computed_at.strftime("%Y-%m-%d %H:%M:%S"),
            h.worker_type,
            h.unit_price,
            request_data.get("order_quantity", ""),
            h.total_price,
            request_data.get("length", ""),
            request_data.get("width", ""),
            request_data.get("thickness", ""),
            request_data.get("color_count", ""),
            request_data.get("area_ratio", ""),
        ])
    
    # 调整列宽
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"quotation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
