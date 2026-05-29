import pandas as pd
import numpy as np
import os

def load_and_clean_data(file_path):
    """
    读取原始 CSV 数据并进行预处理。
    如果文件不存在，会生成一份模拟数据供开发测试使用。
    """
    # ==========================================
    # 0. 容错处理：如果没有找到文件，生成模拟数据
    # ==========================================
    if not os.path.exists(file_path):
        print(f"⚠️ 未找到 {file_path}，正在生成模拟数据供测试...")
        # 生成包含故意制造的“脏数据”（如空值、带$符号的价格）的模拟数据
        mock_data = {
            "Title": ["Spider-Man", "Batman", "X-Men", "Superman", "Avengers", "Wonder Woman", "Flash"],
            "Publisher": ["Marvel", "DC", "Marvel", "DC", "Marvel", "DC", "DC"],
            "Release_Year": [2021, 2021, 2022, 2022, 2023, np.nan, 2023], # 故意放一个空值
            "Unit_Sales": [120000, 115000, np.nan, 95000, 150000, 85000, 70000], # 故意放一个空值
            "Price": ["$3.99", "$4.99", "$3.99", "$4.99", "$5.99", "$3.99", "free"], # 包含特殊字符和非数字
            "Critic_Score": [8.5, 9.0, 7.8, np.nan, 8.8, 8.2, 7.5], # 故意放一个空值
            "Format": ["Single Issue", "Single Issue", "Trade Paperback", "Single Issue", "Graphic Novel", "Single Issue", "Single Issue"]
        }
        df = pd.DataFrame(mock_data)
    else:
        # 1. 读取真实数据
        df = pd.read_csv(file_path)

    # ==========================================
    # 2. 数据清洗：处理异常值与格式转换
    # ==========================================
    
    # 将价格列转换为纯数字浮点数
    # 如果价格是字符串且包含 '$'，我们需要去掉 '$' 并转换为 float。将 'free' 转换为 0。
    if df['Price'].dtype == 'O':  # 'O' 代表 Object/String
        df['Price'] = df['Price'].astype(str).str.replace('$', '', regex=False)
        df['Price'] = df['Price'].replace('free', '0').astype(float)

    # ==========================================
    # 3. 处理缺失值 (Missing Values)
    # ==========================================
    
    # 策略 A：删除缺失核心指标的行 (比如销量未知的数据对我们没有分析价值)
    df = df.dropna(subset=['Unit_Sales'])

    # 策略 B：填充缺失值 (年份缺失用众数填充)
    if 'Release_Year' in df.columns:
        df['Release_Year'] = df['Release_Year'].fillna(df['Release_Year'].mode()[0]).astype(int)

    # 策略 C：分组填充 (将缺失的评分用该出版商的平均分补齐，体现高级数据处理能力)
    if 'Critic_Score' in df.columns:
        df['Critic_Score'] = df.groupby('Publisher')['Critic_Score'].transform(lambda x: x.fillna(x.mean()))
        df['Critic_Score'] = df['Critic_Score'].round(1) # 保留一位小数

    # ==========================================
    # 4. 特征工程 (Feature Engineering)
    # ==========================================
    # 创造新列：总销售额 = 销量 * 单价
    if 'Unit_Sales' in df.columns and 'Price' in df.columns:
        df['Gross_Revenue'] = df['Unit_Sales'] * df['Price']

    print("✅ 数据清洗完成！")
    return df

# 当直接运行此脚本时，执行以下测试代码
if __name__ == "__main__":
    cleaned_df = load_and_clean_data("comic_sales_raw.csv")
    print("\n清洗后的数据前5行：")
    print(cleaned_df.head())
    print("\n清洗后的数据基本信息：")
    print(cleaned_df.info())