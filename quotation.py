import math

# 为了使用表格进行可视化调试，请先安装 prettytable 库
# pip install prettytable
from prettytable import PrettyTable


class QuotationCalculator:
    """
    PVC卡通制品报价计算器。
    该版本通过颜色数量自动确定产量，移除了难度系数。
    """

    def __init__(self):
        # --- 后台参数设定 (可在此处修改参数) ---

        # 利润与损耗
        self.PROFIT_MARGIN = 0.20  # 利润率 (20%)
        self.WASTE_RATE = 0.10  # 废品率 (例如 10%)

        # 材料参数
        self.MATERIAL_DENSITY = 1.166  # 材料密度 (g/cm³)
        self.MATERIAL_PRICE_PER_GRAM = 0.01  # 1g材料价格 (元)

        # 产能参数
        self.MOLD_EDGE_LENGTH = 26  # 模具可用边长 (cm)
        self.MOLD_SPACING = 1  # 产品间距 (cm)
        self.WORKING_DAYS_PER_MONTH = 30  # 每月工作天数
        self.SHIFTS_PER_DAY = 2  # 每日班数

        # !! 新增：颜色数量与单班产量的关系映射表 !!
        # 您可以在此定义不同颜色数量对应的单班生产模具数
        self.COLOR_OUTPUT_MAP = {
            (1, 2): 150,  # 1-2 色 -> 150 模/班 (速度最快)
            (3, 5): 135,  # 3-5 色 -> 135 模/班
            (6, 8): 120,  # 6-8 色 -> 120 模/班 (您提供的基准)
            (9, 11): 100,  # 9-11 色 -> 100 模/班
            (12, 14): 80,  # 12-14 色 -> 80 模/班
            (15, 18): 60,  # 15-18 色 -> 60 模/班 (速度最慢)
        }

        # 机台参数
        self.NEEDLES_PER_MACHINE = 18  # 每台机台的颜色针头数

        # 工人配置
        self.WORKER_PROFILES = {
            "skilled": {"monthly_salary": 8400, "machines_operated": 3},
            "standard": {"monthly_salary": 7000, "machines_operated": 2},
        }

        # 调机与调色费用
        self.SETUP_FEE_PER_COLOR = 20
        self.BASE_SETUP_FEE = 15
        self.COLORING_FEE_PER_COLOR_PER_SHIFT = 5

        # 每个生产单元(cell)每班次的综合成本 (不含工人工资)
        self.OTHER_SALARY_PER_CELL_SHIFT = 50.0
        self.RENT_PER_CELL_SHIFT = 40.0
        self.ELECTRICITY_FEE_PER_CELL_SHIFT = 60.0

    def calculate_quote(
        self,
        length,
        width,
        thickness,
        color_count,
        area_ratio,
        order_quantity,
        worker_type="standard",
        debug=False,
    ):
        """
        计算最终报价。
        :param difficulty_factor: (已移除)
        """
        if debug:
            print("\n" + "=" * 70)
            print(f"====== 开始报价计算 (Debug Mode) | 工人类型: {worker_type} ======")
            t_input = PrettyTable(["输入参数 (Input Parameter)", "数值 (Value)"])
            t_input.align = "l"
            t_input.add_row(["产品长度 (cm)", length])
            t_input.add_row(["产品宽度 (cm)", width])
            t_input.add_row(["产品厚度 (cm)", thickness])
            t_input.add_row(["颜色数量", color_count])
            t_input.add_row(["占用面积比例", area_ratio])
            t_input.add_row(["订单数量", order_quantity])
            print(t_input)

        # --- 第一步：计算产能及生产周期 ---
        units_per_mold = self._calculate_units_per_mold(length, width)
        if units_per_mold == 0:
            return {"error": "产品尺寸过大，无法放入模具"}

        output_per_shift_units, molds_per_shift = self._calculate_output_per_shift(
            units_per_mold, color_count
        )
        if output_per_shift_units == 0:
            return {"error": f"颜色数量({color_count})超出预设范围，无法确定产量"}

        shifts_needed = order_quantity / output_per_shift_units

        if debug:
            t_capacity = PrettyTable(
                ["产能计算 (Capacity Calculation)", "数值 (Value)"]
            )
            t_capacity.align = "l"
            t_capacity.add_row(["每模产品数 (个)", units_per_mold])
            t_capacity.add_row(["根据颜色数确定的单班产模数", molds_per_shift])
            t_capacity.add_row(["单班产量 (个)", f"{output_per_shift_units:.2f}"])
            t_capacity.add_row(["完成订单需要班数", f"{shifts_needed:.2f}"])
            print(t_capacity)

        # --- 后续计算逻辑保持不变 ---
        # 订单材料总成本
        single_material_cost, weight = self._calculate_single_material_cost(
            length, width, thickness, area_ratio
        )
        total_material_cost = single_material_cost * order_quantity

        # 订单班次总成本
        needles_used = color_count + 1
        if needles_used > self.NEEDLES_PER_MACHINE:
            return {
                "error": f"颜色数量过多({color_count}色)，超过机台针头数({self.NEEDLES_PER_MACHINE})"
            }

        cost_per_cell_shift = self._get_cost_per_cell_shift(
            needles_used, color_count, worker_type, debug
        )
        total_shift_cost = cost_per_cell_shift * shifts_needed

        # 调机费
        setup_fee = (color_count * self.SETUP_FEE_PER_COLOR) + self.BASE_SETUP_FEE

        # 订单生产总成本
        total_production_cost = total_material_cost + total_shift_cost + setup_fee

        if debug:
            t_total_cost = PrettyTable(
                ["订单总成本计算 (Total Order Cost)", "数值 (Value)"]
            )
            t_total_cost.align = "l"
            t_total_cost.add_row(["单个产品克重 (g)", f"{weight:.4f}"])
            t_total_cost.add_row(
                ["单个产品材料成本 (元)", f"{single_material_cost:.4f}"]
            )
            t_total_cost.add_row(["订单材料总成本 (元)", f"{total_material_cost:.2f}"])
            t_total_cost.add_row(
                ["单班生产单元综合成本 (元)", f"{cost_per_cell_shift:.2f}"]
            )
            t_total_cost.add_row(["订单班次总成本 (元)", f"{total_shift_cost:.2f}"])
            t_total_cost.add_row(["订单固定调机费 (元)", f"{setup_fee:.2f}"])
            t_total_cost.add_row(
                ["[汇总] 订单生产总成本 (元)", f"{total_production_cost:.2f}"]
            )
            print(t_total_cost)

        # 最终销售单价
        avg_cost_per_unit = total_production_cost / order_quantity
        factory_cost = avg_cost_per_unit / (1 - self.WASTE_RATE)
        selling_price_per_unit = factory_cost * (1 + self.PROFIT_MARGIN)

        # 生成报价单
        total_price = selling_price_per_unit * order_quantity

        if debug:
            t_final = PrettyTable(["最终报价计算 (Final Quotation)", "数值 (Value)"])
            t_final.align = "l"
            t_final.add_row(["单个产品平均生产成本 (元)", f"{avg_cost_per_unit:.4f}"])
            t_final.add_row(["单个产品出厂成本 (含废品率) (元)", f"{factory_cost:.4f}"])
            t_final.add_row(
                ["[最终] 产品销售单价 (元)", f"{selling_price_per_unit:.4f}"]
            )
            t_final.add_row(["[最终] 订单货款总额 (元)", f"{total_price:.2f}"])
            print(t_final)
            print("====== 计算结束 " + "=" * 55 + "\n")

        return {
            "工人类型": worker_type,
            "产品单价": round(selling_price_per_unit, 4),
            "订单货款总额": round(total_price, 2),
            "--- 成本明细 (供内部参考) ---": "",
            "订单数量": order_quantity,
            "需要班数": round(shifts_needed, 2),
            "每模产品数": units_per_mold,
            "单班产量(个)": round(output_per_shift_units),
            "单个产品材料成本": round(single_material_cost, 4),
            "单个产品平均生产成本": round(avg_cost_per_unit, 4),
            "单个产品出厂成本(含废品率)": round(factory_cost, 4),
        }

    def _calculate_units_per_mold(self, length, width):
        """计算一板模具可以放多少个产品"""
        if (length + self.MOLD_SPACING) > self.MOLD_EDGE_LENGTH or (
            width + self.MOLD_SPACING
        ) > self.MOLD_EDGE_LENGTH:
            return 0

        cols = math.floor(self.MOLD_EDGE_LENGTH / (width + self.MOLD_SPACING))
        rows = math.floor(self.MOLD_EDGE_LENGTH / (length + self.MOLD_SPACING))
        return cols * rows

    def _get_molds_per_shift_by_color(self, color_count):
        """根据颜色数量从映射表中查找单班产模数"""
        for (min_colors, max_colors), molds in self.COLOR_OUTPUT_MAP.items():
            if min_colors <= color_count <= max_colors:
                return molds
        return 0  # 如果颜色数超出范围，返回0

    def _calculate_output_per_shift(self, units_per_mold, color_count):
        """计算单个班次的产量 (个)，同时返回产模数"""
        output_in_molds = self._get_molds_per_shift_by_color(color_count)
        if output_in_molds == 0:
            return 0, 0
        output_in_units = output_in_molds * units_per_mold
        return output_in_units, output_in_molds

    def _calculate_single_material_cost(self, length, width, thickness, area_ratio):
        """计算单个产品的材料成本, 同时返回克重"""
        volume = length * width * thickness
        weight = volume * area_ratio * self.MATERIAL_DENSITY
        cost = weight * self.MATERIAL_PRICE_PER_GRAM
        return cost, weight

    def _get_cost_per_cell_shift(
        self, needles_used, color_count, worker_type, debug=False
    ):
        """计算一个生产单元（例如1个工人+N台机器）单个班次的总成本。"""
        profile = self.WORKER_PROFILES.get(worker_type)
        if not profile:
            raise ValueError(f"未知的工人类型: {worker_type}")

        monthly_salary = profile["monthly_salary"]
        machines_operated = profile["machines_operated"]

        worker_salary_per_shift = monthly_salary / (
            self.WORKING_DAYS_PER_MONTH * self.SHIFTS_PER_DAY
        )

        total_cell_cost_per_shift = (
            worker_salary_per_shift
            + self.OTHER_SALARY_PER_CELL_SHIFT
            + self.RENT_PER_CELL_SHIFT
            + self.ELECTRICITY_FEE_PER_CELL_SHIFT
        )

        base_cost_per_machine_shift = total_cell_cost_per_shift / machines_operated

        machine_cost_allocation_factor = needles_used / self.NEEDLES_PER_MACHINE
        allocated_cost_per_machine = (
            base_cost_per_machine_shift * machine_cost_allocation_factor
        )

        total_allocated_machine_cost = allocated_cost_per_machine * machines_operated

        total_coloring_fee = color_count * self.COLORING_FEE_PER_COLOR_PER_SHIFT

        final_cost = total_allocated_machine_cost + total_coloring_fee

        if debug:
            t_shift = PrettyTable(
                ["班次成本分解 (Shift Cost Breakdown)", "数值 (Value)"]
            )
            t_shift.align = "l"
            t_shift.add_row(["工人单班工资 (元)", f"{worker_salary_per_shift:.2f}"])
            t_shift.add_row(
                ["生产单元(Cell)单班总成本 (元)", f"{total_cell_cost_per_shift:.2f}"]
            )
            t_shift.add_row(
                ["分摊到单台机器的成本 (元)", f"{base_cost_per_machine_shift:.2f}"]
            )
            t_shift.add_row(
                ["产品使用针头数", f"{needles_used} / {self.NEEDLES_PER_MACHINE}"]
            )
            t_shift.add_row(["机台成本占用率", f"{machine_cost_allocation_factor:.2%}"])
            t_shift.add_row(
                ["产品分摊的机台成本(元/台)", f"{allocated_cost_per_machine:.2f}"]
            )
            t_shift.add_row(
                ["产品分摊的单元总成本(元/班)", f"{total_allocated_machine_cost:.2f}"]
            )
            t_shift.add_row(["班次调色总费用 (元)", f"{total_coloring_fee:.2f}"])
            t_shift.add_row(["[汇总] 单班生产单元综合成本 (元)", f"{final_cost:.2f}"])
            print(t_shift)

        return final_cost


# --- 示例：如何使用这个计算器 ---
if __name__ == "__main__":
    import os
    import sys
    
    # 添加项目路径以导入应用模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # 尝试使用数据库配置
        from app.services.calculator_service import build_calculator_from_db
        from app.db.session import SessionLocal
        
        print("使用数据库配置进行计算...")
        db = SessionLocal()
        calculator = build_calculator_from_db(db)
        db.close()
        
        print(f"当前配置 - 利润率: {calculator.PROFIT_MARGIN:.1%}, 每月工作天数: {calculator.WORKING_DAYS_PER_MONTH}天")
        
    except ImportError as e:
        print(f"无法导入数据库模块 ({e})，使用默认配置...")
        calculator = QuotationCalculator()
        print(f"默认配置 - 利润率: {calculator.PROFIT_MARGIN:.1%}, 每月工作天数: {calculator.WORKING_DAYS_PER_MONTH}天")

    # 2. 定义产品参数 (已移除 difficulty_factor)
    product_info = {
        "length": 3,  # 产品长度 (cm)
        "width": 2.5,  # 产品宽度 (cm)
        "thickness": 0.4,  # 产品厚度 (cm)
        "color_count": 2,  # !! 请修改此处测试不同颜色 !!
        "area_ratio": 0.85,  # 占用面积比例 (70%)
        "order_quantity": 100000,  # 订单数量
    }

    # 3. 以 Debug 模式进行计算
    calculator.calculate_quote(**product_info, worker_type="standard", debug=True)

    # 4. 如果您只想获取最终结果，不看过程，可以设置 debug=False
    print("\n--- [正式报价] ---")
    final_quote = calculator.calculate_quote(
        **product_info, worker_type="standard", debug=False
    )
    for key, value in final_quote.items():
        if "---" not in key:
            print(f"{key}: {value}")
