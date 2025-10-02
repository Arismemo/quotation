from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class WorkerProfileSchema(BaseModel):
    name: str
    monthly_salary: float = Field(..., gt=0)
    machines_operated: int = Field(..., gt=0)
    
    class Config:
        from_attributes = True


class AppSettingsSchema(BaseModel):
    # 利润与损耗
    profit_margin: Optional[float] = Field(None, gt=0, le=1)
    waste_rate: Optional[float] = Field(None, ge=0, lt=1)
    
    # 材料参数
    material_density: Optional[float] = Field(None, gt=0)
    material_price_per_gram: Optional[float] = Field(None, gt=0)
    
    # 产能参数
    mold_edge_length: Optional[float] = Field(None, gt=0)
    mold_spacing: Optional[float] = Field(None, ge=0)
    base_molds_per_shift: Optional[float] = Field(None, gt=0)
    working_days_per_month: Optional[int] = Field(None, gt=0)
    shifts_per_day: Optional[int] = Field(None, gt=0)
    
    # 机台参数
    needles_per_machine: Optional[int] = Field(None, gt=0)
    
    # 调机与调色费用
    setup_fee_per_color: Optional[float] = Field(None, ge=0)
    base_setup_fee: Optional[float] = Field(None, ge=0)
    coloring_fee_per_color_per_shift: Optional[float] = Field(None, ge=0)
    
    # 生产单元成本
    other_salary_per_cell_shift: Optional[float] = Field(None, ge=0)
    rent_per_cell_shift: Optional[float] = Field(None, ge=0)
    electricity_fee_per_cell_shift: Optional[float] = Field(None, ge=0)
    
    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    settings: AppSettingsSchema
    worker_profiles: List[WorkerProfileSchema]


class SettingsUpdateRequest(BaseModel):
    settings: Optional[AppSettingsSchema] = None
    worker_profiles: Optional[List[WorkerProfileSchema]] = None


