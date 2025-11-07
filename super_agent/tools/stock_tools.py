import akshare as ak
import re
from pydantic import Field, BaseModel
from typing import List
import datetime
import asyncio
from oxygent.oxy import FunctionHub
from currency_converter import CurrencyConverter

stock_tools = FunctionHub(name="stock_tools")


class HKStockHistData(BaseModel):
    """港股历史数据模型"""
    date: datetime.datetime
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: int
    amount: float
    amplitude: float
    change_percent: float
    change_amount: float
    turnover_rate: float

    @classmethod
    def from_dataframe_row(cls, row) -> "HKStockHistData":
        """从DataFrame行数据创建HKStockHistData实例"""
        return cls(
            date=datetime.datetime.strptime(str(row["日期"]), "%Y-%m-%d"),
            open_price=float(row["开盘"]),
            close_price=float(row["收盘"]),
            high_price=float(row["最高"]),
            low_price=float(row["最低"]),
            volume=int(row["成交量"]),
            amount=float(row["成交额"]),
            amplitude=float(row["振幅"]),
            change_percent=float(row["涨跌幅"]),
            change_amount=float(row["涨跌额"]),
            turnover_rate=float(row["换手率"])
        )


class HKStockHistResponse(BaseModel):
    """港股历史数据响应模型"""
    symbol: str
    data: List[HKStockHistData]
    total_count: int

    @classmethod
    def from_dataframe(cls, df: str, symbol: str) -> "HKStockHistResponse":
        """从DataFrame创建HKStockHistResponse实例"""
        data_list = [HKStockHistData.from_dataframe_row(row) for _, row in df.iterrows()]
        return cls(
            symbol=symbol,
            data=data_list,
            total_count=len(data_list)
        )


class USStockHistData(BaseModel):
    """美股历史数据模型"""
    date: datetime.datetime
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: int
    amount: float
    amplitude: float
    change_percent: float
    change_amount: float
    turnover_rate: float

    @classmethod
    def from_dataframe_row(cls, row) -> "USStockHistData":
        """从DataFrame行数据创建USStockHistData实例"""
        return cls(
            date=datetime.datetime.strptime(str(row["日期"]), "%Y-%m-%d"),
            open_price=float(row["开盘"]),
            close_price=float(row["收盘"]),
            high_price=float(row["最高"]),
            low_price=float(row["最低"]),
            volume=int(row["成交量"]),
            amount=float(row["成交额"]),
            amplitude=float(row["振幅"]),
            change_percent=float(row["涨跌幅"]),
            change_amount=float(row["涨跌额"]),
            turnover_rate=float(row["换手率"])
        )


class USStockHistResponse(BaseModel):
    """美股历史数据响应模型"""
    symbol: str
    data: List[USStockHistData]
    total_count: int

    @classmethod
    def from_dataframe(cls, df, symbol: str) -> "USStockHistResponse":
        """从DataFrame创建USStockHistResponse实例"""
        data_list = [USStockHistData.from_dataframe_row(row) for _, row in df.iterrows()]
        return cls(
            symbol=symbol,
            data=data_list,
            total_count=len(data_list)
        )


@stock_tools.tool(
description="""
返回港股股票历史数据
股价全部以USD计
""")
def fecth_hk_stock_data(
    symbol: str = Field(symbol="股票代码，只允许数字，如09618"),
    date = Field(description="股票日期，如20170628")
) -> str:
    # 验证股票代码格式 - 只允许数字
    if not symbol.isdigit():
        raise ValueError(f"股票代码格式错误：'{symbol}' 包含非数字字符。股票代码应只包含数字，例如：09618")

    # 验证日期格式 - 应为YYYYMMDD格式的8位数字
    if not re.match(r'^\d{8}$', date):
        raise ValueError(f"日期格式错误：'{date}' 不是有效的格式。日期应为8位数字格式，例如：20170628")

    # 验证日期的合理性
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])

    if month < 1 or month > 12:
        raise ValueError(f"日期格式错误：月份 '{month}' 无效。月份应在1-12之间")

    if day < 1 or day > 31:
        raise ValueError(f"日期格式错误：日期 '{day}' 无效。日期应在1-31之间")
    
    hk_df = ak.stock_hk_hist(symbol=symbol, period="daily", start_date=date, end_date=date, adjust="")
    hk_data_list = HKStockHistResponse.from_dataframe(hk_df, symbol).data
    if(len(hk_data_list) == 0):
        raise ValueError("未找到指定日期的港股数据")
    hk_data = hk_data_list[0]
    hk_data.open_price = convertHKD2USD(hk_data.open_price, hk_data.date)
    hk_data.close_price = convertHKD2USD(hk_data.close_price, hk_data.date)
    hk_data.high_price = convertHKD2USD(hk_data.high_price, hk_data.date)
    hk_data.low_price = convertHKD2USD(hk_data.low_price, hk_data.date)

    return hk_data.model_dump_json()



@stock_tools.tool(
description="""
返回美股股票历史数据
股价全部以USD计
""")
def fecth_us_stock_data(
    symbol: str = Field(symbol="股票代码，如105.JD"),
    date = Field(description="股票日期，如20170628")
) -> str:
    # 验证日期格式 - 应为YYYYMMDD格式的8位数字
    if not re.match(r'^\d{8}$', date):
        raise ValueError(f"日期格式错误：'{date}' 不是有效的格式。日期应为8位数字格式，例如：20170628")

    # 验证日期的合理性
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])

    if month < 1 or month > 12:
        raise ValueError(f"日期格式错误：月份 '{month}' 无效。月份应在1-12之间")

    if day < 1 or day > 31:
        raise ValueError(f"日期格式错误：日期 '{day}' 无效。日期应在1-31之间")
    stock_us_hist_df = ak.stock_us_hist(symbol=symbol, period="daily", start_date=date, end_date=date, adjust="qfq")
    us_data_list = HKStockHistResponse.from_dataframe(stock_us_hist_df, symbol).data
    if(len(us_data_list) == 0):
        raise ValueError("未找到指定日期的港股数据")
    us_data = us_data_list[0]
    return us_data.model_dump_json() 


def convertHKD2USD(amount: float, date: datetime):
    c = CurrencyConverter()
    converted_amount = c.convert(amount, 'HKD', 'USD', date=date)
    print(f"{date}: {amount} HKD = {converted_amount:.2f} USD")
    return converted_amount







async def test_fecth_hk_stock_data():
    """异步测试 fecth_hk_stock_data 函数"""
    try:
        print("开始测试 fecth_hk_stock_data 函数...")

        # 测试用例 1: 正常港股代码
        symbol = "09618"  # 港股-美团
        date = "20220628"

        print(f"\n测试用例 1: 获取港股 {symbol} 在 {date} 的数据")
        result = await fecth_hk_stock_data(symbol, date)
        print(result)

        # 测试用例 2: 错误的股票代码
        print(f"\n测试用例 2: 测试错误的股票代码")
        try:
            await fecth_hk_stock_data("ABC123", "20220628")
        except ValueError as e:
            print(f"✅ 正确捕获错误: {e}")

        # 测试用例 3: 错误的日期格式
        print(f"\n测试用例 3: 测试错误的日期格式")
        try:
            await fecth_hk_stock_data("09618", "2022-06-28")
        except ValueError as e:
            print(f"✅ 正确捕获错误: {e}")

        # 测试用例 4: 不存在的日期
        print(f"\n测试用例 4: 测试不存在的日期")
        try:
            await fecth_hk_stock_data("09618", "20221225")  # 周末可能无数据
            print("✅ 周末日期测试完成")
        except ValueError as e:
            print(f"✅ 正确捕获错误: {e}")

        print("\n🎉 所有测试完成!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise

async def test_fecth_us_stock_data():
    """异步测试 fecth_us_stock_data 函数"""
    try:
        print("开始测试 fecth_hk_stock_data 函数...")

        symbol = "105.JD"  
        date = "20220628"

        print(f"\n测试用例 1: 获取美股 {symbol} 在 {date} 的数据")
        result = await fecth_us_stock_data(symbol, date)
        print(result)


    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise



# 使用示例和测试
if __name__ == "__main__":
    print("运行异步测试...")
    # asyncio.run(test_fecth_hk_stock_data())
    # print("\n" + "="*50)
    # names = ak.get_us_stock_name()
    # print(names) 
    asyncio.run(test_fecth_us_stock_data())
    # stock_us_spot_em_df = ak.stock_us_spot_em()
    # print(stock_us_spot_em_df)