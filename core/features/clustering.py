from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from core.constants import LABEL_ORDER, YEAR_COLUMN_CANDIDATES


def perform_advanced_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    全局聚类主函数。
    仅在全量数据上执行一次，结果固化至 DataFrame 列，供所有下游 UI 使用。

    新增列：
        Cluster                  int   KMeans 原始簇编号
        Cluster_Label            str   商业语义标签（保证无 NaN）
        PCA1 / PCA2              float 降维坐标
        Silhouette_Score         float 轮廓系数（全局常量列）
        PCA_Explained_Variance   float PCA 方差解释率（全局常量列）
        Sales_Num / Price_Num / Rating_Num / Issue_Num  float 归一前数值列

    标签映射规则（多维复合，优先级递进）：
        Blockbuster ← 最高 0.6*sales_norm + 0.4*issue_norm
        Event       ← 剩余中最高 0.7*sales_norm - 0.3*issue_norm
        Premium     ← 剩余中最高 0.5*price_norm + 0.5*rating_norm
        Long Tail   ← 最后剩余的簇（也作为 NaN 兜底默认值）
    """
    ml_df = df.copy()

    # ── 1. Issue_Num：-1 保留 Annual/Special/One-Shot 的业务语义 ──────────────
    issue_text = (
        ml_df["Issue"] if "Issue" in ml_df.columns
        else pd.Series(["1"] * len(ml_df))
    ).astype(str)
    ml_df["Issue_Num"] = (
        issue_text.str.extract(r"(\d+)")[0]
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
    n_clusters = min(4, len(ml_df))
    if n_clusters < 2:
        ml_df["Cluster"]               = 0
        ml_df["Cluster_Label"]         = LABEL_ORDER[-1]   # Long Tail
        ml_df["Silhouette_Score"]      = 0.0
        ml_df["PCA1"]                  = 0.0
        ml_df["PCA2"]                  = 0.0
        ml_df["PCA_Explained_Variance"] = 0.0
        return ml_df

    # ── 9. KMeans ─────────────────────────────────────────────────────────────
    kmeans = KMeans(
        n_clusters=n_clusters, init="k-means++",
        n_init=20, max_iter=500, random_state=42,
    )
    ml_df["Cluster"] = kmeans.fit_predict(X)

    # ── 10. Silhouette Score ──────────────────────────────────────────────────
    sil_score = (
        silhouette_score(X, ml_df["Cluster"])
        if ml_df["Cluster"].nunique() > 1 else 0.0
    )
    ml_df["Silhouette_Score"] = sil_score

    # ── 11. PCA 降维 ──────────────────────────────────────────────────────────
    n_components = min(2, len(ml_df), X.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    pca_result = pca.fit_transform(X)
    ml_df["PCA1"] = pca_result[:, 0]
    ml_df["PCA2"] = pca_result[:, 1] if n_components > 1 else 0.0
    ml_df["PCA_Explained_Variance"] = pca.explained_variance_ratio_.sum()

    # ── 12. 稳定的多维复合商业语义映射 ───────────────────────────────────────
    #
    # 归一化各簇统计均值至 [0,1]，消除量纲差异后按优先级规则依次分配标签。
    #
    # 实际权重（注意：下方注释是文档，请勿与代码脱节）：
    #   Blockbuster : 0.6 * sales_norm + 0.4 * issue_norm
    #   Event       : 0.7 * sales_norm - 0.3 * issue_norm  （高销低期）
    #   Premium     : 0.5 * price_norm + 0.5 * rating_norm
    #   Long Tail   : 剩余（也作为 NaN 兜底默认值）
    #
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

    # 规则 1：Blockbuster = 高销量 + 高期数（持续主线 IP）
    scores = norm["sales_mean"] * 0.6 + norm["issue_mean"] * 0.4
    best = scores[list(remaining)].idxmax()
    mapping[best] = LABEL_ORDER[0]
    remaining.discard(best)

    # 规则 2：Event = 高销量 + 低期数（#1 创刊号 / 联动爆发）
    if remaining:
        scores = norm["sales_mean"] * 0.7 - norm["issue_mean"] * 0.3
        best = scores[list(remaining)].idxmax()
        mapping[best] = LABEL_ORDER[1]
        remaining.discard(best)

    # 规则 3：Premium = 高价格 + 高评分（精品限定）
    if remaining:
        scores = norm["price_mean"] * 0.5 + norm["rating_mean"] * 0.5
        best = scores[list(remaining)].idxmax()
        mapping[best] = LABEL_ORDER[2]
        remaining.discard(best)

    # 规则 4：Long Tail = 最后剩余
    for cid in remaining:
        mapping[cid] = LABEL_ORDER[3]

    # ── 修复③：fillna 兜底，保证 n_clusters < 4 时不产生 NaN ─────────────────
    # 旧写法：ml_df["Cluster_Label"] = ml_df["Cluster"].map(mapping)
    # 当 n_clusters=2 时 mapping 只有 2 个键，其余行 map 返回 NaN
    ml_df["Cluster_Label"] = (
        ml_df["Cluster"]
        .map(mapping)
        .fillna(LABEL_ORDER[-1])   # 未覆盖的簇全部归入 Long Tail
    )

    return ml_df