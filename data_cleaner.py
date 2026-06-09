import pandas as pd
import re
from core.config import DEFAULT_DATA_FILE, ENRICHED_DATA_FILE, ENRICHED_FIELDS

COLUMN_ALIASES = {
    "units": "Rank", "rank": "Rank", "title": "Title", "issue": "Issue", "price": "Price",
    "publisher": "Studio/Pub", "studio": "Studio/Pub", "sales": "Unit Sales", 
    "unit_sales": "Unit Sales", "release_year": "Release Year", "Release_Year": "Release Year"
}

def clean_text(value, default=""):
    if pd.isna(value): return default
    return str(value).strip()

def load_and_clean_comic_data(file_path=None):
    # 路径决策优先级：传入路径 > 富化路径 > 默认路径
    target_path = file_path or (ENRICHED_DATA_FILE if ENRICHED_DATA_FILE.exists() else DEFAULT_DATA_FILE)
    
    try:
        df = pd.read_excel(target_path) if str(target_path).endswith('.xlsx') else pd.read_csv(target_path)
    except Exception as e:
        raise ValueError(f"无法读取数据文件: {target_path}, 错误: {e}")

    # 1. 列名标准化
    df = df.rename(columns=lambda x: COLUMN_ALIASES.get(str(x).strip().lower(), x))
    df = df.rename(columns=COLUMN_ALIASES)

    # 2. 核心列清洗
    df["Title"] = df["Title"].map(clean_text)
    df["Issue"] = df["Issue"].map(lambda v: clean_text(v, "1")) if "Issue" in df.columns else "1"
    df["Studio/Pub"] = df["Studio/Pub"].map(lambda v: clean_text(v, "Independent"))
    
    # 标题规范化（去除 #、Vol. 等信息，方便后续匹配）
    df["Norm_Title"] = df["Title"].str.replace(r'#\d+|Vol\.?\s*\d+', '', regex=True, flags=re.IGNORECASE).str.strip()

    # 3. 销售数据处理 (处理可能存在的千分位符)
    if "Unit Sales" in df.columns:
        df["Unit Sales"] = df["Unit Sales"].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df["Unit Sales"] = pd.to_numeric(df["Unit Sales"], errors="coerce").fillna(0).astype(int)
    
    # 4. 年份健壮性处理
    if "Release Year" not in df.columns:
        df["Release Year"] = 2026
    df["Release Year"] = pd.to_numeric(df["Release Year"], errors="coerce")
    median_year = df["Release Year"].median()
    df["Release Year"] = df["Release Year"].fillna(median_year if not pd.isna(median_year) else 2026).astype(int)

    # 5. 其他数值指标
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0).astype(float)
    df["Rating"] = pd.to_numeric(df.get("Rating", pd.NA), errors="coerce")
    df["Page Count"] = pd.to_numeric(df.get("Page Count", pd.NA), errors="coerce")

    # 6. 富化字段填充
    invalid_strs = {"unknown", "none", "nan", "null", "not available", ""}
    for col in ENRICHED_FIELDS:
        if col not in df.columns:
            df[col] = "Not Enriched"
        else:
            df[col] = df[col].astype(str).map(clean_text)
            mask = df[col].str.lower().isin(invalid_strs) | df[col].isna()
            df.loc[mask, col] = "Not Available"
            
    return df
