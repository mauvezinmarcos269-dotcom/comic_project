from __future__ import annotations

import re
from collections import Counter

import pandas as pd
import statsmodels.api as sm

from core.constants import YEAR_COLUMN_CANDIDATES, N_CLUSTERS
from core.features.clustering import perform_advanced_clustering

def perform_pca_clustering(df: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> pd.DataFrame | None:
    # 修复：向下透传 n_clusters 参数
    result = perform_advanced_clustering(df.copy(), n_clusters=n_clusters)
    
    if result is None or result.empty:
        return None
    
    required_cols = ["Cluster", "PCA1", "PCA2", "Cluster_Label"]
    for col in required_cols:
        if col not in result.columns:
            return None
    
    if "Title" not in result.columns and "Norm_Title" in result.columns:
        result["Title"] = result["Norm_Title"]
    
    return result

def extract_title_keywords(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
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

def perform_regression(df: pd.DataFrame) -> tuple[pd.DataFrame | None, str | None]:
    # 修复：动态获取销量列
    sales_col = next(
        (c for c in ["Unit Sales", "sales"] if c in df.columns), None
    )
    if sales_col is None:
        return None, None

    analysis_df = df[["Price", sales_col]].dropna()
    analysis_df = analysis_df[analysis_df["Price"] > 0]
    if len(analysis_df) < 5:
        return None, None

    X = sm.add_constant(analysis_df[["Price"]], has_constant="add")
    y = analysis_df[sales_col]
    model = sm.OLS(y, X).fit()
    result_df = analysis_df.copy()
    result_df["Predicted_Sales"] = model.predict(X)
    return result_df, str(model.summary())

def get_special_decade_ranking(
    df: pd.DataFrame, start: int = 2010, end: int = 2019
) -> tuple[pd.Series, list[tuple]]:
    year_col = next(
        (c for c in YEAR_COLUMN_CANDIDATES if c in df.columns), None
    )
    if year_col is None:
        return pd.Series(dtype=float), []

    subset = df[(df[year_col] >= start) & (df[year_col] <= end)]
    title_col = next(
        (c for c in ("Norm_Title", "Title") if c in subset.columns), None
    )
    
    # 修复：动态获取销量列
    sales_col = next(
        (c for c in ["Unit Sales", "sales"] if c in subset.columns), None
    )
    
    if title_col is None or sales_col is None or subset.empty:
        return pd.Series(dtype=float), []

    ranking = (
        subset.groupby(title_col)[sales_col]
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