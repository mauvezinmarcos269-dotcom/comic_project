from __future__ import annotations

import re
from collections import Counter

import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from core.constants import YEAR_COLUMN_CANDIDATES, N_CLUSTERS
from core.features.clustering import perform_advanced_clustering


def perform_pca_clustering(df: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> pd.DataFrame | None:
    """
    轻量 PCA 聚类，仅供 AI 问答路由（executor.py pca_cluster 模块）使用。
    内部复用 perform_advanced_clustering 的核心逻辑，确保与全局聚类一致。

    Args:
        df:          输入 DataFrame
        n_clusters:  KMeans 簇数（默认使用全局常量 N_CLUSTERS）

    Returns:
        带有 Cluster / PCA1 / PCA2 / Title / Studio/Pub 列的 DataFrame，
        若样本不足则返回 None。
    """
    # 直接调用全局聚类逻辑，确保一致性
    result = perform_advanced_clustering(df.copy())
    
    # 检查是否有足够的聚类结果
    if result is None or result.empty:
        return None
    
    # 保留必要的列用于可视化
    required_cols = ["Cluster", "PCA1", "PCA2", "Cluster_Label"]
    for col in required_cols:
        if col not in result.columns:
            return None
    
    # 确保 Title 和 Studio/Pub 存在
    if "Title" not in result.columns and "Norm_Title" in result.columns:
        result["Title"] = result["Norm_Title"]
    
    return result


def extract_title_keywords(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """统计标题高频词，优先使用 Norm_Title，回退到 Title。"""
    target_col = next(
        (c for c in ("Norm_Title", "Title") if c in df.columns), None
    )
    if target_col is None or df.empty:
        return pd.DataFrame(columns=["Word", "Frequency"])

    stop_words = {
        "the", "a", "of", "and", "in", "to", "for",
        "vs", "vol", "issue", "comic", "comics", "is",
    }
    all_words: list[str] = []
    for title in df[target_col].dropna():
        words = re.findall(r"\\b[a-zA-Z]{3,}\\b", str(title).lower())
        all_words.extend(w for w in words if w not in stop_words)

    word_counts = Counter(all_words).most_common(top_n)
    return pd.DataFrame(word_counts, columns=["Word", "Frequency"])


def perform_regression(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame | None, str | None]:
    """OLS 回归：价格 → 销量。样本不足时返回 (None, None)。"""
    analysis_df = df[["Price", "Unit Sales"]].dropna()
    analysis_df = analysis_df[analysis_df["Price"] > 0]
    if len(analysis_df) < 5:
        return None, None

    # 修复：使用 DataFrame 而非 Series，确保类型稳定
    X = sm.add_constant(analysis_df[["Price"]], has_constant="add")
    y = analysis_df["Unit Sales"]
    model = sm.OLS(y, X).fit()
    result_df = analysis_df.copy()
    result_df["Predicted_Sales"] = model.predict(X)
    return result_df, str(model.summary())


def get_special_decade_ranking(
    df: pd.DataFrame, start: int = 2010, end: int = 2019
) -> tuple[pd.Series, list[tuple]]:
    """返回指定年代段的漫画系列总销量 Top 10 及特殊系列注记。"""
    year_col = next(
        (c for c in YEAR_COLUMN_CANDIDATES if c in df.columns), None
    )
    if year_col is None:
        return pd.Series(dtype=float), []

    subset = df[(df[year_col] >= start) & (df[year_col] <= end)]
    title_col = next(
        (c for c in ("Norm_Title", "Title") if c in subset.columns), None
    )
    if title_col is None or subset.empty:
        return pd.Series(dtype=float), []

    ranking = (
        subset.groupby(title_col)["Unit Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    target_series = ["star wars", "detective comics", "amazing spider-man"]
    special_notes = [
        (title, sales)
        for title, sales in ranking.items()
        if any(ts in str(title).lower() for ts in target_series)
    ]
    return ranking, special_notes