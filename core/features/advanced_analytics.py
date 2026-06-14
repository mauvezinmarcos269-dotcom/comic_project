from __future__ import annotations

import re
from collections import Counter

import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from core.constants import YEAR_COLUMN_CANDIDATES


def perform_pca_clustering(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame | None:
    """
    轻量 PCA 聚类，仅供 AI 问答路由（executor.py pca_cluster 模块）使用。
    不用于 dashboard 或 cluster_probe —— 那两个组件统一使用
    core.features.clustering.perform_advanced_clustering 的结果。

    修复：Release Year 列名动态查找，避免列名差异导致 KeyError。

    Args:
        df:          输入 DataFrame
        n_clusters:  KMeans 簇数

    Returns:
        带有 Cluster / PCA1 / PCA2 / Title / Studio/Pub 列的 DataFrame，
        若样本不足则返回 None。
    """
    # ── 修复⑥：动态查找年份列，兼容 "Release Year" / "Release_Year" / "Year" ──
    year_col = next(
        (c for c in YEAR_COLUMN_CANDIDATES if c in df.columns), None
    )
    if year_col is None:
        # 三种候选列都不存在时，跳过年份特征而非抛出 KeyError
        base_features = ["Unit Sales", "Price"]
    else:
        base_features = ["Unit Sales", "Price", year_col]

    analysis_df = df[base_features].dropna().copy()
    if len(analysis_df) < max(10, n_clusters):
        return None

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(analysis_df)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    analysis_df["Cluster"] = kmeans.fit_predict(scaled_data)

    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    analysis_df["PCA1"] = pca_result[:, 0]
    analysis_df["PCA2"] = pca_result[:, 1]

    # 回填原始 DataFrame 中的标题与出版商，方便悬停显示
    for col in ("Title", "Studio/Pub"):
        if col in df.columns:
            analysis_df[col] = df.loc[analysis_df.index, col]

    return analysis_df


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
        words = re.findall(r"\b[a-zA-Z]{3,}\b", str(title).lower())
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

    X = sm.add_constant(analysis_df["Price"])
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