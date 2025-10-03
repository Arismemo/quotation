import math
# 为了使用表格进行可视化调试，请先安装 prettytable 库
# pip install prettytable
from prettytable import PrettyTable

class QuotationCalculator:
    """
    PVC卡通制品报价计算器。
    根据V2.1方案实现，该版本不包含一次性模具费。
    """
    def __init__(self):
        # --- 后台参数设定 (可在此处修改参数) ---

        # 利润与损耗
        self.PROFIT_MARGIN = 0.30  # 利润率 (例如 30%)
        self.WASTE_RATE = 0.10     # 废品率 (例如 10%)

        # 材料参数
        self.MATERIAL_DENSITY = 1.166      # 材料密度 (g/cm³)
        self.MATERIAL_PRICE_PER_GRAM = 0.01  # 1g材料价格 (元)

        # 产能参数
        self.MOLD_EDGE_LENGTH = 26      # 模具可用边长 (cm)
        self.MOLD_SPACING = 1           # 产品间距 (cm)
        self.BASE_MOLDS_PER_SHIFT = 120 # 单班基准产模数 (难度系数为3时)
        self.WORKING_DAYS_PER_MONTH = 26 # 每月工作天数
        self.SHIFTS_PER_DAY = 2         # 每日班数
        
        # 机台参数
        self.NEEDLES_PER_MACHINE = 18 # 每台机台的颜色针头数

        # 工人配置 (新增)
        self.WORKER_PROFILES = {
            "skilled": {"monthly_salary": 8400, "machines_operated": 3},
            "standard": {"monthly_salary": 7000, "machines_operated": 2}
        }

        # 调机与调色费用
        self.SETUP_FEE_PER_COLOR = 20  # 单个颜色调机费用
        self.BASE_SETUP_FEE = 15       # 基础调机费
        self.COLORING_FEE_PER_COLOR_PER_SHIFT = 5  # 单个颜色单班调色费用 (适用于整个班组)

        # 每个生产单元(cell)每班次的综合成本 (不含工人工资)
        self.OTHER_SALARY_PER_CELL_SHIFT = 50.0
        self.RENT_PER_CELL_SHIFT = 40.0
        self.ELECTRICITY_FEE_PER_CELL_SHIFT = 60.0


    def calculate_quote(self, length, width, thickness, color_count, area_ratio, difficulty_factor, order_quantity, worker_type="standard", debug=False):
        """
        计算最终报价。

        :param debug: 是否打印详细计算过程
        ... (其他参数不变)
        """
        if debug:
            print("\n" + "="*70)
            print(f"====== 开始报价计算 (Debug Mode) | 工人类型: {worker_type} ======")
            t_input = PrettyTable(["输入参数 (Input Parameter)", "数值 (Value)"])
            t_input.align = "l"
            t_input.add_row(["产品长度 (cm)", length])
            t_input.add_row(["产品宽度 (cm)", width])
            t_input.add_row(["产品厚度 (cm)", thickness])
            t_input.add_row(["颜色数量", color_count])
            t_input.add_row(["占用面积比例", area_ratio])
            t_input.add_row(["难度系数", difficulty_factor])
            t_input.add_row(["订单数量", order_quantity])
            print(t_input)

        # --- 第一步：计算产能及生产周期 ---
        units_per_mold = self._calculate_units_per_mold(length, width)
        if units_per_mold == 0:
            return {"error": "产品尺寸过大，无法放入模具"}

        output_per_shift_units = self._calculate_output_per_shift(units_per_mold, difficulty_factor)
        if output_per_shift_units == 0:
            return {"error": "单班产量为0，请检查难度系数是否为0"}
        # 根据您的要求，移除 math.ceil，允许班数为小数，以实现更精确的成本计算
        shifts_needed = order_quantity / output_per_shift_units

        if debug:
            t_capacity = PrettyTable(["产能计算 (Capacity Calculation)", "数值 (Value)"])
            t_capacity.align = "l"
            t_capacity.add_row(["每模产品数 (个)", units_per_mold])
            t_capacity.add_row(["单班产量 (个)", f"{output_per_shift_units:.2f}"])
            # 更新调试信息的打印格式，以显示小数班次
            t_capacity.add_row(["完成订单需要班数", f"{shifts_needed:.2f}"])
            print(t_capacity)

        # --- 第二步：计算订单各项成本明细 ---
        # 订单材料总成本
        single_material_cost, weight = self._calculate_single_material_cost(length, width, thickness, area_ratio)
        total_material_cost = single_material_cost * order_quantity
        
        # 订单班次总成本
        needles_used = color_count + 1
        if needles_used > self.NEEDLES_PER_MACHINE:
            return {"error": f"颜色数量过多({color_count}色)，超过机台针头数({self.NEEDLES_PER_MACHINE})"}

        cost_per_cell_shift = self._get_cost_per_cell_shift(needles_used, color_count, worker_type, debug)
        total_shift_cost = cost_per_cell_shift * shifts_needed

        # 调机费
        setup_fee = (color_count * self.SETUP_FEE_PER_COLOR) + self.BASE_SETUP_FEE

        # --- 第三步：计算订单生产总成本 ---
        total_production_cost = total_material_cost + total_shift_cost + setup_fee

        if debug:
            t_total_cost = PrettyTable(["订单总成本计算 (Total Order Cost)", "数值 (Value)"])
            t_total_cost.align = "l"
            t_total_cost.add_row(["单个产品克重 (g)", f"{weight:.4f}"])
            t_total_cost.add_row(["单个产品材料成本 (元)", f"{single_material_cost:.4f}"])
            t_total_cost.add_row(["订单材料总成本 (元)", f"{total_material_cost:.2f}"])
            t_total_cost.add_row(["单班生产单元综合成本 (元)", f"{cost_per_cell_shift:.2f}"])
            t_total_cost.add_row(["订单班次总成本 (元)", f"{total_shift_cost:.2f}"])
            t_total_cost.add_row(["订单固定调机费 (元)", f"{setup_fee:.2f}"])
            t_total_cost.add_row(["[汇总] 订单生产总成本 (元)", f"{total_production_cost:.2f}"])
            print(t_total_cost)


        # --- 第四步：计算最终销售单价 ---
        avg_cost_per_unit = total_production_cost / order_quantity
        factory_cost = avg_cost_per_unit / (1 - self.WASTE_RATE)
        selling_price_per_unit = factory_cost * (1 + self.PROFIT_MARGIN)

        # --- 第五步：生成报价单 ---
        total_price = selling_price_per_unit * order_quantity
        
        if debug:
            t_final = PrettyTable(["最终报价计算 (Final Quotation)", "数值 (Value)"])
            t_final.align = "l"
            t_final.add_row(["单个产品平均生产成本 (元)", f"{avg_cost_per_unit:.4f}"])
            t_final.add_row(["单个产品出厂成本 (含废品率) (元)", f"{factory_cost:.4f}"])
            t_final.add_row(["[最终] 产品销售单价 (元)", f"{selling_price_per_unit:.4f}"])
            t_final.add_row(["[最终] 订单货款总额 (元)", f"{total_price:.2f}"])
            print(t_final)
            print("====== 计算结束 " + "="*55 + "\n")

        return {
            "工人类型": worker_type,
            "产品单价": round(selling_price_per_unit, 4),
            "订单货款总额": round(total_price, 2),
            "--- 成本明细 (供内部参考) ---": "",
            "订单数量": order_quantity,
            "需要班数": shifts_needed,
            "每模产品数": units_per_mold,
            "单班产量(个)": round(output_per_shift_units),
            "单个产品材料成本": round(single_material_cost, 4),
            "单个产品平均生产成本": round(avg_cost_per_unit, 4),
            "单个产品出厂成本(含废品率)": round(factory_cost, 4),
        }

    def _calculate_units_per_mold(self, length, width):
        """计算一板模具可以放多少个产品"""
        if (length + self.MOLD_SPACING) > self.MOLD_EDGE_LENGTH or \
           (width + self.MOLD_SPACING) > self.MOLD_EDGE_LENGTH:
            return 0
        
        cols = math.floor(self.MOLD_EDGE_LENGTH / (width + self.MOLD_SPACING))
        rows = math.floor(self.MOLD_EDGE_LENGTH / (length + self.MOLD_SPACING))
        return cols * rows

    def _calculate_output_per_shift(self, units_per_mold, difficulty_factor):
        """计算单个班次的产量 (个)"""
        # 难度系数为3是基准产量, 所以用 (3 / difficulty_factor) 作为调整系数
        if difficulty_factor == 0:
            return 0
        output_in_molds = self.BASE_MOLDS_PER_SHIFT * (3 / difficulty_factor)
        return output_in_molds * units_per_mold
    
    def _calculate_single_material_cost(self, length, width, thickness, area_ratio):
        """计算单个产品的材料成本, 同时返回克重"""
        volume = length * width * thickness
        weight = volume * area_ratio * self.MATERIAL_DENSITY
        cost = weight * self.MATERIAL_PRICE_PER_GRAM
        return cost, weight

    def _get_cost_per_cell_shift(self, needles_used, color_count, worker_type, debug=False):
        """
        计算一个生产单元（例如1个工人+N台机器）单个班次的总成本。
        """
        # 1. 获取工人配置
        profile = self.WORKER_PROFILES.get(worker_type)
        if not profile:
            raise ValueError(f"未知的工人类型: {worker_type}")
        
        monthly_salary = profile["monthly_salary"]
        machines_operated = profile["machines_operated"]

        # 2. 计算该工人的单班工资
        worker_salary_per_shift = monthly_salary / (self.WORKING_DAYS_PER_MONTH * self.SHIFTS_PER_DAY)

        # 3. 计算整个生产单元(1个工人+N台机器)的单班总成本
        total_cell_cost_per_shift = (worker_salary_per_shift +
                                     self.OTHER_SALARY_PER_CELL_SHIFT +
                                     self.RENT_PER_CELL_SHIFT +
                                     self.ELECTRICITY_FEE_PER_CELL_SHIFT)
        
        # 4. 将单元成本分摊到单台机器上
        base_cost_per_machine_shift = total_cell_cost_per_shift / machines_operated

        # 5. 根据针头占用比例，计算产品应分摊的机台成本
        machine_cost_allocation_factor = needles_used / self.NEEDLES_PER_MACHINE
        allocated_cost_per_machine = base_cost_per_machine_shift * machine_cost_allocation_factor

        # 6. 计算整个生产单元(N台机器)的总分摊成本
        total_allocated_machine_cost = allocated_cost_per_machine * machines_operated

        # 7. 加上适用于整个班组的调色费用
        total_coloring_fee = color_count * self.COLORING_FEE_PER_COLOR_PER_SHIFT
        
        final_cost = total_allocated_machine_cost + total_coloring_fee

        if debug:
            t_shift = PrettyTable(["班次成本分解 (Shift Cost Breakdown)", "数值 (Value)"])
            t_shift.align = "l"
            t_shift.add_row(["工人单班工资 (元)", f"{worker_salary_per_shift:.2f}"])
            t_shift.add_row(["生产单元(Cell)单班总成本 (元)", f"{total_cell_cost_per_shift:.2f}"])
            t_shift.add_row(["分摊到单台机器的成本 (元)", f"{base_cost_per_machine_shift:.2f}"])
            t_shift.add_row(["产品使用针头数", f"{needles_used} / {self.NEEDLES_PER_MACHINE}"])
            t_shift.add_row(["机台成本占用率", f"{machine_cost_allocation_factor:.2%}"])
            t_shift.add_row(["产品分摊的机台成本(元/台)", f"{allocated_cost_per_machine:.2f}"])
            t_shift.add_row(["产品分摊的单元总成本(元/班)", f"{total_allocated_machine_cost:.2f}"])
            t_shift.add_row(["班次调色总费用 (元)", f"{total_coloring_fee:.2f}"])
            t_shift.add_row(["[汇总] 单班生产单元综合成本 (元)", f"{final_cost:.2f}"])
            print(t_shift)

        return final_cost


# --- 示例：如何使用这个计算器 ---
if __name__ == "__main__":
    # 1. 创建计算器实例
    calculator = QuotationCalculator()

    # 2. 定义产品参数 (请在此处修改为您想计算的产品信息)
    product_info = {
        "length": 5.2,            # 产品长度 (cm)
        "width": 3.5,             # 产品宽度 (cm)
        "thickness": 0.3,         # 产品厚度 (cm)
        "color_count": 6,         # 颜色数量
        "area_ratio": 0.9,        # 占用面积比例 (70%)
        "difficulty_factor": 3,   # 难度系数 (3为普通)
        "order_quantity": 6000    # 订单数量
    }

    # 3. 以 Debug 模式进行计算
    # 您会看到详细的计算过程表格
    calculator.calculate_quote(**product_info, worker_type="skilled", debug=False)

    # 4. 如果您只想获取最终结果，不看过程，可以设置 debug=False
    print("\n--- [正式报价] ---")
    final_quote = calculator.calculate_quote(**product_info, worker_type="skilled", debug=False)
    for key, value in final_quote.items():
        if "---" not in key:
            print(f"{key}: {value}")


