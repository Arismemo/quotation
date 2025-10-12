import os
import sys

from sqlalchemy.orm import Session

# 导入原始计算器（从项目根目录）
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from quotation import QuotationCalculator
from app.services.cache_service import get_cached_settings, get_cached_worker_profiles


def build_calculator_from_db(db: Session) -> QuotationCalculator:
    """从数据库设置构建计算器实例"""

    # 获取应用设置（使用缓存）
    settings = get_cached_settings(db)
    if not settings:
        raise ValueError("应用设置未初始化")

    # 获取工人配置（使用缓存）
    worker_profiles_list = get_cached_worker_profiles(db)

    # 创建计算器实例
    calc = QuotationCalculator()

    # 覆盖设置
    calc.PROFIT_MARGIN = settings["profit_margin"]
    calc.WASTE_RATE = settings["waste_rate"]
    calc.MATERIAL_DENSITY = settings["material_density"]
    calc.MATERIAL_PRICE_PER_GRAM = settings["material_price_per_gram"]
    calc.MOLD_EDGE_LENGTH = settings["mold_edge_length"]
    calc.MOLD_SPACING = settings["mold_spacing"]
    # 注意：BASE_MOLDS_PER_SHIFT 已移除，现在使用 COLOR_OUTPUT_MAP
    calc.WORKING_DAYS_PER_MONTH = settings["working_days_per_month"]
    calc.SHIFTS_PER_DAY = settings["shifts_per_day"]
    calc.NEEDLES_PER_MACHINE = settings["needles_per_machine"]
    calc.SETUP_FEE_PER_COLOR = settings["setup_fee_per_color"]
    calc.BASE_SETUP_FEE = settings["base_setup_fee"]
    calc.COLORING_FEE_PER_COLOR_PER_SHIFT = settings["coloring_fee_per_color_per_shift"]
    calc.OTHER_SALARY_PER_CELL_SHIFT = settings["other_salary_per_cell_shift"]
    calc.RENT_PER_CELL_SHIFT = settings["rent_per_cell_shift"]
    calc.ELECTRICITY_FEE_PER_CELL_SHIFT = settings["electricity_fee_per_cell_shift"]

    # 覆盖工人配置
    calc.WORKER_PROFILES = {
        profile["name"]: {
            "monthly_salary": profile["monthly_salary"],
            "machines_operated": profile["machines_operated"],
        }
        for profile in worker_profiles_list
    }

    # 配置颜色产能映射
    try:
        if settings["color_output_map"]:
            # 期望格式：[{"min_colors":1,"max_colors":2,"molds_per_shift":150}, ...]
            color_map = {}
            for item in settings["color_output_map"]:
                min_c = int(item.get("min_colors"))
                max_c = int(item.get("max_colors"))
                molds = float(item.get("molds_per_shift"))
                color_map[(min_c, max_c)] = molds
            # 仅当映射非空时覆盖
            if color_map:
                calc.COLOR_OUTPUT_MAP = color_map
    except Exception:
        # 保持计算器默认映射
        pass

    return calc


def compute_quote(
    db: Session,
    length: float,
    width: float,
    thickness: float,
    color_count: int,
    area_ratio: float,
    order_quantity: int,
    worker_type: str = "standard",
    debug: bool = False,
) -> dict:
    """执行报价计算"""

    calc = build_calculator_from_db(db)

    # 如果开启调试模式，收集详细的中间计算数据
    if debug:
        debug_info = _collect_debug_info(calc, length, width, thickness, color_count, area_ratio, order_quantity, worker_type)
        result = calc.calculate_quote(
            length=length,
            width=width,
            thickness=thickness,
            color_count=color_count,
            area_ratio=area_ratio,
            order_quantity=order_quantity,
            worker_type=worker_type,
            debug=False,  # 不打印到控制台
        )
        # 将调试信息添加到结果中
        result["debug_info"] = debug_info
    else:
        result = calc.calculate_quote(
            length=length,
            width=width,
            thickness=thickness,
            color_count=color_count,
            area_ratio=area_ratio,
            order_quantity=order_quantity,
            worker_type=worker_type,
            debug=False,
        )

    # 如果返回错误，抛出异常
    if "error" in result:
        raise ValueError(result["error"])

    # 追加单个产品克重（g）
    try:
        _cost, weight_g = calc._calculate_single_material_cost(
            length, width, thickness, area_ratio
        )
        result["单个产品克重(g)"] = round(weight_g, 4)
    except Exception:
        pass

    return result


def _collect_debug_info(calc, length, width, thickness, color_count, area_ratio, order_quantity, worker_type):
    """收集调试信息"""
    debug_info = {}
    
    # 1. 输入参数
    debug_info["input_params"] = {
        "产品长度(cm)": length,
        "产品宽度(cm)": width,
        "产品厚度(cm)": thickness,
        "颜色数量": color_count,
        "占用面积比例": area_ratio,
        "订单数量": order_quantity,
        "工人类型": worker_type
    }
    
    # 2. 产能计算
    units_per_mold = calc._calculate_units_per_mold(length, width)
    output_per_shift_units, molds_per_shift = calc._calculate_output_per_shift(units_per_mold, color_count)
    shifts_needed = order_quantity / output_per_shift_units
    
    debug_info["capacity_calculation"] = {
        "每模产品数(个)": units_per_mold,
        "根据颜色数确定的单班产模数": molds_per_shift,
        "单班产量(个)": round(output_per_shift_units, 2),
        "完成订单需要班数": round(shifts_needed, 2)
    }
    
    # 3. 材料成本计算
    single_material_cost, weight = calc._calculate_single_material_cost(length, width, thickness, area_ratio)
    total_material_cost = single_material_cost * order_quantity
    
    debug_info["material_cost"] = {
        "单个产品克重(g)": round(weight, 4),
        "单个产品材料成本(元)": round(single_material_cost, 4),
        "订单材料总成本(元)": round(total_material_cost, 2)
    }
    
    # 4. 班次成本计算
    needles_used = color_count + 1
    cost_per_cell_shift = calc._get_cost_per_cell_shift(needles_used, color_count, worker_type, debug=False)
    total_shift_cost = cost_per_cell_shift * shifts_needed
    
    debug_info["shift_cost"] = {
        "产品使用针头数": f"{needles_used} / {calc.NEEDLES_PER_MACHINE}",
        "单班生产单元综合成本(元)": round(cost_per_cell_shift, 2),
        "订单班次总成本(元)": round(total_shift_cost, 2)
    }
    
    # 5. 调机费计算
    setup_fee = (color_count * calc.SETUP_FEE_PER_COLOR) + calc.BASE_SETUP_FEE
    
    debug_info["setup_cost"] = {
        "订单固定调机费(元)": round(setup_fee, 2)
    }
    
    # 6. 总成本计算
    total_production_cost = total_material_cost + total_shift_cost + setup_fee
    avg_cost_per_unit = total_production_cost / order_quantity
    factory_cost = avg_cost_per_unit / (1 - calc.WASTE_RATE)
    selling_price_per_unit = factory_cost * (1 + calc.PROFIT_MARGIN)
    total_price = selling_price_per_unit * order_quantity
    
    debug_info["total_cost"] = {
        "订单生产总成本(元)": round(total_production_cost, 2),
        "单个产品平均生产成本(元)": round(avg_cost_per_unit, 4),
        "单个产品出厂成本(含废品率)(元)": round(factory_cost, 4),
        "产品销售单价(元)": round(selling_price_per_unit, 4),
        "订单货款总额(元)": round(total_price, 2)
    }
    
    # 7. 系统参数
    debug_info["system_params"] = {
        "利润率": f"{calc.PROFIT_MARGIN:.1%}",
        "废品率": f"{calc.WASTE_RATE:.1%}",
        "材料密度(g/cm³)": calc.MATERIAL_DENSITY,
        "材料价格(元/g)": calc.MATERIAL_PRICE_PER_GRAM,
        "模具可用边长(cm)": calc.MOLD_EDGE_LENGTH,
        "产品间距(cm)": calc.MOLD_SPACING,
        "每月工作天数": calc.WORKING_DAYS_PER_MONTH,
        "每日班数": calc.SHIFTS_PER_DAY,
        "每台机台针头数": calc.NEEDLES_PER_MACHINE,
        "调机费/颜色(元)": calc.SETUP_FEE_PER_COLOR,
        "基础调机费(元)": calc.BASE_SETUP_FEE,
        "调色费/颜色/班(元)": calc.COLORING_FEE_PER_COLOR_PER_SHIFT
    }
    
    # 8. 工人配置
    worker_profile = calc.WORKER_PROFILES.get(worker_type, {})
    debug_info["worker_profile"] = {
        "工人类型": worker_type,
        "月薪(元)": worker_profile.get("monthly_salary", 0),
        "操作机台数": worker_profile.get("machines_operated", 0)
    }
    
    # 9. 颜色产能映射
    debug_info["color_output_map"] = {}
    for (min_colors, max_colors), molds_per_shift in calc.COLOR_OUTPUT_MAP.items():
        key = f"{min_colors}-{max_colors}色"
        debug_info["color_output_map"][key] = f"{molds_per_shift} 模/班"
    
    return debug_info
