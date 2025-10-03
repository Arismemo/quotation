import sys
import os
from sqlalchemy.orm import Session
from app.db import crud
from typing import Dict

# 导入原始计算器（从项目根目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from quotation import QuotationCalculator


def build_calculator_from_db(db: Session) -> QuotationCalculator:
    """从数据库设置构建计算器实例"""
    
    # 获取应用设置
    settings = crud.get_app_settings(db)
    if not settings:
        raise ValueError("应用设置未初始化")
    
    # 获取工人配置
    worker_profiles_list = crud.get_worker_profiles(db)
    
    # 创建计算器实例
    calc = QuotationCalculator()
    
    # 覆盖设置
    calc.PROFIT_MARGIN = settings.profit_margin
    calc.WASTE_RATE = settings.waste_rate
    calc.MATERIAL_DENSITY = settings.material_density
    calc.MATERIAL_PRICE_PER_GRAM = settings.material_price_per_gram
    calc.MOLD_EDGE_LENGTH = settings.mold_edge_length
    calc.MOLD_SPACING = settings.mold_spacing
    calc.BASE_MOLDS_PER_SHIFT = settings.base_molds_per_shift
    calc.WORKING_DAYS_PER_MONTH = settings.working_days_per_month
    calc.SHIFTS_PER_DAY = settings.shifts_per_day
    calc.NEEDLES_PER_MACHINE = settings.needles_per_machine
    calc.SETUP_FEE_PER_COLOR = settings.setup_fee_per_color
    calc.BASE_SETUP_FEE = settings.base_setup_fee
    calc.COLORING_FEE_PER_COLOR_PER_SHIFT = settings.coloring_fee_per_color_per_shift
    calc.OTHER_SALARY_PER_CELL_SHIFT = settings.other_salary_per_cell_shift
    calc.RENT_PER_CELL_SHIFT = settings.rent_per_cell_shift
    calc.ELECTRICITY_FEE_PER_CELL_SHIFT = settings.electricity_fee_per_cell_shift
    
    # 覆盖工人配置
    calc.WORKER_PROFILES = {
        profile.name: {
            "monthly_salary": profile.monthly_salary,
            "machines_operated": profile.machines_operated
        }
        for profile in worker_profiles_list
    }
    
    return calc


def compute_quote(db: Session, 
                  length: float, 
                  width: float, 
                  thickness: float,
                  color_count: int,
                  area_ratio: float,
                  difficulty_factor: float,
                  order_quantity: int,
                  worker_type: str = "standard",
                  debug: bool = False) -> Dict:
    """执行报价计算"""
    
    calc = build_calculator_from_db(db)
    
    result = calc.calculate_quote(
        length=length,
        width=width,
        thickness=thickness,
        color_count=color_count,
        area_ratio=area_ratio,
        difficulty_factor=difficulty_factor,
        order_quantity=order_quantity,
        worker_type=worker_type,
        debug=debug
    )
    
    # 如果返回错误，抛出异常
    if "error" in result:
        raise ValueError(result["error"])
    
    # 追加单个产品克重（g）
    try:
        _cost, weight_g = calc._calculate_single_material_cost(length, width, thickness, area_ratio)
        result["单个产品克重(g)"] = round(weight_g, 4)
    except Exception:
        pass

    return result


