from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from typing import cast

from core.constants import LABEL_ORDER, YEAR_COLUMN_CANDIDATES, N_CLUSTERS

def perform_advanced_clustering(df: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> pd.DataFrame:
    """
    全局聚类主函数。
    仅在全量数据上执行一次，结果固化至 DataFrame 列，供所有下游 UI 使用。
    """
    ml_df = df.copy()

    # ── 1. Issue_Num：-1 保留 Annual/Special/One-Shot 的业务语义 ──────────────
    issue_text = (
        ml_df["Issue"] if "Issue" in ml_df.columns
        else pd.Series(["1"] * len(ml_df))
    )
    # 修复正则提取逻辑，确保安全提取数字
    ml_df["Issue_Num"] = (
        issue_text.astype(str)
        .str.extract(r"(\d+)")[0]
        .fillna(-1)
        .astype(int)
    )

    # ── 2. Price_Num ──────────────────────────────────────────────────────────
    price_series = ml_df.get("Price", pd.Series([0.0] * len(ml_df)))
    ml_df["Price_Num"] = pd.to_numeric(price_series, errors="coerce").fillna(0.0)

    # ── 3. Sales_Num ──────────────────────────────────────────────────────────
    sales_series = ml_df.get(
        "Unit Sales",
        ml_df.get("sales", pd.Series([0] * len(ml_df)))
    )
    ml_df["Sales_Num"] = pd.to_numeric(sales_series, errors="coerce").fillna(0)

    # ── 4. Rating_Num ─────────────────────────────────────────────────────────
    rating_series = ml_df.get("Rating", pd.Series(dtype=float))
    rating_num = pd.to_numeric(rating_series, errors="coerce")
    rating_median = rating_num.median()
    ml_df["Rating_Num"] = rating_num.fillna(
        rating_median if pd.notna(rating_median) else 3.0
    )

    # ── 5. Year_Num（从 constants 共享候选列表）───────────────────────────────
    year_col = next(
        (c for c in YEAR_COLUMN_CANDIDATES if c in ml_df.columns), None
    )
    year_series = ml_df[year_col] if year_col else pd.Series([2026] * len(ml_df))
    ml_df["Year_Num"] = pd.to_numeric(year_series, errors="coerce").fillna(2026).astype(int)

    # ── 6. 安全因子化 ──────────────────────────────────────────────────────────
    def safe_factorize(candidates: list[str]) -> pd.Series:
        col = next((c for c in candidates if c in ml_df.columns), None)
        series = (
            ml_df[col] if col
            else pd.Series(["Unknown"] * len(ml_df), dtype="object")
        )
        return pd.Series(pd.factorize(series.fillna("Unknown"))[0], index=ml_df.index)

    ml_df["Publisher_Code"] = safe_factorize(
        ["Studio/Pub", "Publisher", "publisher", "Studio", "Pub"]
    )
    ml_df["ComicType_Code"] = safe_factorize(
        ["Comic_Type", "comic_type", "Comic Type"]
    )

    # ── 7. 特征矩阵 ────────────────────────────────────────────────────────────
    features = [
        "Sales_Num", "Issue_Num", "Price_Num", "Rating_Num",
        "Publisher_Code", "Year_Num", "ComicType_Code",
    ]
    X = StandardScaler().fit_transform(ml_df[features])

    # ── 8. 小样本保护 ──────────────────────────────────────────────────────────
    # 修复：动态采用传入的 n_clusters
    actual_clusters = min(n_clusters, len(ml_df))
    if actual_clusters < 2:
        ml_df["Cluster"]                = 0
        ml_df["Cluster_Label"]          = LABEL_ORDER[-1]   # Long Tail
        ml_df["Silhouette_Score"]       = 0.0
        ml_df["PCA1"]                   = 0.0
        ml_df["PCA2"]                   = 0.0
        ml_df["PCA_Explained_Variance"] = 0.0
        return ml_df

    # ── 9. KMeans ─────────────────────────────────────────────────────────────
    kmeans = KMeans(
        n_clusters=actual_clusters, init="k-means++",
        n_init=20, max_iter=500, random_state=42,
    )
    ml_df["Cluster"] = kmeans.fit_predict(X)

    # ── 10. Silhouette Score ──────────────────────────────────────────────────
    n_unique = ml_df["Cluster"].nunique()
    if n_unique > 1 and len(ml_df) > n_unique:
        sil_score = float(silhouette_score(X, ml_df["Cluster"]))
    else:
        sil_score = 0.0
    ml_df["Silhouette_Score"] = sil_score

    # ── 11. PCA 降维 ──────────────────────────────────────────────────────────
    n_components = min(2, len(ml_df), X.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    pca_result = pca.fit_transform(X)
    ml_df["PCA1"] = pca_result[:, 0]
    ml_df["PCA2"] = pca_result[:, 1] if n_components > 1 else 0.0

    variance_ratio = float(pca.explained_variance_ratio_.sum())
    ml_df["PCA_Explained_Variance"] = 0.0 if pd.isna(variance_ratio) else variance_ratio

    # ── 12. 稳定的多维复合商业语义映射 ───────────────────────────────────────
    cluster_stats = ml_df.groupby("Cluster").agg(
        sales_mean  = ("Sales_Num",  "mean"),
        issue_mean  = ("Issue_Num",  "mean"),
        price_mean  = ("Price_Num",  "mean"),
        rating_mean = ("Rating_Num", "mean"),
    )
    norm = pd.DataFrame(
        MinMaxScaler().fit_transform(cluster_stats),
        columns=cluster_stats.columns,
        index=cluster_stats.index,
    )

    remaining = set(cluster_stats.index)
    mapping: dict[int, str] = {}

    if remaining:
        scores = norm["sales_mean"] * 0.6 + norm["issue_mean"] * 0.4
        best = cast(int, scores[list(remaining)].idxmax())
        mapping[best] = LABEL_ORDER[0]
        remaining.discard(best)

    if remaining:
        scores = norm["sales_mean"] * 0.7 - norm["issue_mean"] * 0.3
        best = cast(int, scores[list(remaining)].idxmax())
        mapping[best] = LABEL_ORDER[1]
        remaining.discard(best)

    if remaining:
        scores = norm["price_mean"] * 0.5 + norm["rating_mean"] * 0.5
        best = cast(int, scores[list(remaining)].idxmax())
        mapping[best] = LABEL_ORDER[2]
        remaining.discard(best)

    for cid in remaining:
        mapping[cid] = LABEL_ORDER[3]

    ml_df["Cluster_Label"] = (
        ml_df["Cluster"]
        .map(mapping)
        .fillna(LABEL_ORDER[-1])
    )

    return ml_df