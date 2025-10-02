import math

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
        self.MOLD_EDGE_LENGTH = 26  # 模具可用边长 (cm)
        self.MOLD_SPACING = 1       # 产品间距 (cm)
        self.SHIFTS_PER_DAY = 2     # 每日班数
        self.BASE_MOLDS_PER_SHIFT = 120 # 单班基准产模数 (难度系数为3时)

        # 调机与调色费用
        self.SETUP_FEE_PER_COLOR = 20  # 单个颜色调机费用
        self.BASE_SETUP_FEE = 15       # 基础调机费
        self.COLORING_FEE_PER_COLOR_PER_SHIFT = 5  # 单个颜色单班调色费用 (估算值)

        # 每班次综合成本 (非材料)
        self.WORKER_SALARY_PER_SHIFT = 288.5  # 单班工人工资
        self.OTHER_SALARY_PER_SHIFT = 50.0    # 单班其它职位工资 (估算值)
        self.RENT_PER_SHIFT = 40.0            # 单班房租 (估算值)
        self.ELECTRICITY_FEE_PER_SHIFT = 60.0 # 单班电费 (估算值)

    def calculate_quote(self, length, width, thickness, color_count, area_ratio, difficulty_factor, order_quantity):
        """
        计算最终报价。

        :param length: 产品长度 (cm)
        :param width: 产品宽度 (cm)
        :param thickness: 产品厚度 (cm)
        :param color_count: 颜色数量
        :param area_ratio: 占用面积比例 (例如 0.7 表示 70%)
        :param difficulty_factor: 难度系数 (例如 3 表示普通难度)
        :param order_quantity: 订单数量 (个)
        :return: 包含报价详情的字典
        """
        # --- 第三步：计算每次订单的生产总成本 ---

        # 1. 计算产能及生产周期
        units_per_mold = self._calculate_units_per_mold(length, width)
        if units_per_mold == 0:
            return {"error": "产品尺寸过大，无法放入模具"}

        output_per_shift_units = self._calculate_output_per_shift(units_per_mold, difficulty_factor)
        shifts_needed = math.ceil(order_quantity / output_per_shift_units)

        # 2. 计算订单各项成本明细
        # 订单材料总成本
        single_material_cost = self._calculate_single_material_cost(length, width, thickness, area_ratio)
        total_material_cost = single_material_cost * order_quantity

        # 订单班次总成本
        cost_per_shift = self._get_cost_per_shift(color_count)
        total_shift_cost = cost_per_shift * shifts_needed

        # 调机费 (每次订单固定)
        setup_fee = (color_count * self.SETUP_FEE_PER_COLOR) + self.BASE_SETUP_FEE

        # 3. 计算订单生产总成本
        total_production_cost = total_material_cost + total_shift_cost + setup_fee

        # --- 第四步：计算最终销售单价 ---

        # 1. 计算单个产品平均成本
        avg_cost_per_unit = total_production_cost / order_quantity

        # 2. 计算出厂成本 (含废品率)
        factory_cost = avg_cost_per_unit / (1 - self.WASTE_RATE)

        # 3. 计算最终销售单价
        selling_price_per_unit = factory_cost * (1 + self.PROFIT_MARGIN)

        # --- 第五步：生成报价单 ---
        total_price = selling_price_per_unit * order_quantity

        return {
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
        """计算单个产品的材料成本"""
        volume = length * width * thickness
        weight = volume * area_ratio * self.MATERIAL_DENSITY
        return weight * self.MATERIAL_PRICE_PER_GRAM

    def _get_cost_per_shift(self, color_count):
        """计算一个班次的总综合成本"""
        total_coloring_fee = color_count * self.COLORING_FEE_PER_COLOR_PER_SHIFT
        return (self.WORKER_SALARY_PER_SHIFT + 
                self.OTHER_SALARY_PER_SHIFT +
                self.RENT_PER_SHIFT +
                self.ELECTRICITY_FEE_PER_SHIFT +
                total_coloring_fee)

# --- 示例：如何使用这个计算器 ---
if __name__ == "__main__":
    # 1. 创建计算器实例
    calculator = QuotationCalculator()

    # 2. 定义产品参数 (请在此处修改为您想计算的产品信息)
    product_info = {
        "length": 3,            # 产品长度 (cm)
        "width": 3,             # 产品宽度 (cm)
        "thickness": 0.3,         # 产品厚度 (cm)
        "color_count": 5,         # 颜色数量
        "area_ratio": 0.7,        # 占用面积比例 (70%)
        "difficulty_factor": 3,   # 难度系数 (3为普通)
        "order_quantity": 5000    # 订单数量
    }

    # 3. 执行计算
    quote = calculator.calculate_quote(**product_info)

    # 4. 打印结果
    print("--- 报价计算结果 ---")
    for key, value in quote.items():
        if "---" in key:
            print(f"\n{key}")
        else:
            print(f"{key}: {value}")
