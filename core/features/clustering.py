import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def perform_advanced_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    全局聚类主函数。
    仅在全量数据上执行一次，结果固化至 DataFrame 列，供所有下游 UI 使用。

    新增列：
        Cluster           int   KMeans 原始簇编号
        Cluster_Label     str   商业语义标签
        PCA1 / PCA2       float 降维坐标
        Silhouette_Score  float 轮廓系数（全局常量列）
        PCA_Explained_Variance float PCA 方差解释率（全局常量列）
        Sales_Num / Price_Num / Rating_Num / Issue_Num  float  归一前数值列
    """
    ml_df = df.copy()

    # ── 1. 数值列安全提取 ──────────────────────────────────────────────────────
    issue_text = (
        ml_df["Issue"] if "Issue" in ml_df.columns
        else pd.Series(["1"] * len(ml_df))
    ).astype(str)

    ml_df["Issue_Num"] = (
        issue_text.str.extract(r"(\d+)")[0]
        .fillna(-1)          # -1 保留 Annual/Special/One-Shot 的业务语义
        .astype(int)
    )

    price_series = (
        ml_df["Price"] if "Price" in ml_df.columns
        else pd.Series([0.0] * len(ml_df))
    )
    ml_df["Price_Num"] = pd.to_numeric(price_series, errors="coerce").fillna(0.0)

    if "Unit Sales" in ml_df.columns:
        sales_series = ml_df["Unit Sales"]
    elif "sales" in ml_df.columns:
        sales_series = ml_df["sales"]
    else:
        sales_series = pd.Series([0] * len(ml_df))
    ml_df["Sales_Num"] = pd.to_numeric(sales_series, errors="coerce").fillna(0)

    rating_series = (
        ml_df["Rating"] if "Rating" in ml_df.columns
        else pd.Series(dtype=float)
    )
    rating_median = pd.to_numeric(rating_series, errors="coerce").median()
    ml_df["Rating_Num"] = pd.to_numeric(rating_series, errors="coerce").fillna(
        rating_median if not pd.isna(rating_median) else 3.0
    )

    # ── 2. Release Year 动态兼容 ───────────────────────────────────────────────
    year_col = next(
        (c for c in ["Release Year", "Release_Year", "Year", "release_year"] if c in ml_df.columns),
        None,
    )
    year_series = ml_df[year_col] if year_col else pd.Series([2026] * len(ml_df))
    ml_df["Year_Num"] = pd.to_numeric(year_series, errors="coerce").fillna(2026).astype(int)

    # ── 3. 安全因子化 ──────────────────────────────────────────────────────────
    def safe_factorize(column_candidates: list[str]) -> pd.Series:
        col = next((c for c in column_candidates if c in ml_df.columns), None)
        series = ml_df[col] if col else pd.Series(["Unknown"] * len(ml_df), dtype="object")
        return pd.Series(pd.factorize(series.fillna("Unknown"))[0], index=ml_df.index)

    ml_df["Publisher_Code"] = safe_factorize(["Studio/Pub", "Publisher", "publisher", "Studio", "Pub"])
    ml_df["ComicType_Code"] = safe_factorize(["Comic_Type", "comic_type", "Comic Type"])

    # ── 4. 特征矩阵 ────────────────────────────────────────────────────────────
    features = [
        "Sales_Num", "Issue_Num", "Price_Num", "Rating_Num",
        "Publisher_Code", "Year_Num", "ComicType_Code",
    ]
    X = StandardScaler().fit_transform(ml_df[features])

    # ── 5. 小样本保护 ──────────────────────────────────────────────────────────
    n_clusters = min(4, len(ml_df))
    if n_clusters < 2:
        ml_df["Cluster"] = 0
        ml_df["Cluster_Label"] = "Unknown"
        ml_df["Silhouette_Score"] = 0.0
        ml_df["PCA1"] = 0.0
        ml_df["PCA2"] = 0.0
        ml_df["PCA_Explained_Variance"] = 0.0
        return ml_df

    # ── 6. KMeans ──────────────────────────────────────────────────────────────
    kmeans = KMeans(
        n_clusters=n_clusters, init="k-means++",
        n_init=20, max_iter=500, random_state=42,
    )
    ml_df["Cluster"] = kmeans.fit_predict(X)

    # ── 7. Silhouette Score ───────────────────────────────────────────────────
    sil_score = (
        silhouette_score(X, ml_df["Cluster"])
        if ml_df["Cluster"].nunique() > 1 else 0.0
    )
    ml_df["Silhouette_Score"] = sil_score

    # ── 8. PCA 降维 ───────────────────────────────────────────────────────────
    n_components = min(2, len(ml_df), X.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    pca_result = pca.fit_transform(X)
    ml_df["PCA1"] = pca_result[:, 0]
    ml_df["PCA2"] = pca_result[:, 1] if n_components > 1 else 0.0
    ml_df["PCA_Explained_Variance"] = pca.explained_variance_ratio_.sum()

    # ── 9. 稳定的多维复合商业语义映射（建议七的改进实现）─────────────────────
    #
    # 原方案：仅按 Sales_Num 均值排序 → Premium 与 Event 易互换
    # 新方案：复合评分排序，每个簇按加权得分匹配最合适的商业标签
    #
    # 规则（优先级递进）：
    #   Blockbuster ← 高销量 AND 高期数（持续连载的主线 IP）
    #   Event       ← 高销量 AND 低期数（#1 创刊号 / 年度联动爆发）
    #   Premium     ← 中等销量 AND 高价格 AND 高评分（精品限定）
    #   Long Tail   ← 其余（销量中下游，基数庞大）
    #
    cluster_stats = ml_df.groupby("Cluster").agg(
        sales_mean=("Sales_Num",  "mean"),
        issue_mean=("Issue_Num",  "mean"),
        price_mean=("Price_Num",  "mean"),
        rating_mean=("Rating_Num", "mean"),
    )

    # MinMax 归一化至 [0,1]，消除量纲差异
    from sklearn.preprocessing import MinMaxScaler as _MMS
    norm = pd.DataFrame(
        _MMS().fit_transform(cluster_stats),
        columns=cluster_stats.columns,
        index=cluster_stats.index,
    )

    labels = [
        "Blockbuster IP (大IP主线)",
        "Event Comics (独立大事件)",
        "Premium Series (精品限定)",
        "Long Tail (长尾市场)",
    ]

    remaining = set(cluster_stats.index)
    mapping: dict[int, str] = {}

    # 规则 1：Blockbuster = 最高 (sales + issue) 综合得分
    scores_blockbuster = norm["sales_mean"] * 0.6 + norm["issue_mean"] * 0.4
    best = scores_blockbuster[list(remaining)].idxmax()
    mapping[best] = labels[0]
    remaining.discard(best)

    # 规则 2：Event = 剩余中销量最高但期数最低（高销低期）
    if remaining:
        scores_event = norm["sales_mean"] * 0.7 - norm["issue_mean"] * 0.3
        best = scores_event[list(remaining)].idxmax()
        mapping[best] = labels[1]
        remaining.discard(best)

    # 规则 3：Premium = 剩余中价格+评分综合最高
    if remaining:
        scores_premium = norm["price_mean"] * 0.5 + norm["rating_mean"] * 0.5
        best = scores_premium[list(remaining)].idxmax()
        mapping[best] = labels[2]
        remaining.discard(best)

    # 规则 4：Long Tail = 最后剩余的簇
    for cluster_id in remaining:
        mapping[cluster_id] = labels[3]

    ml_df["Cluster_Label"] = ml_df["Cluster"].map(mapping)
    return ml_df