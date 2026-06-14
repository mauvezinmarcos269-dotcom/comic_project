import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def perform_advanced_clustering(df):
    """
    全局聚类模块
    仅在全量数据上执行一次，避免筛选后簇漂移
    """

    ml_df = df.copy()

    # ==========================================
    # 1. 数值列安全提取
    # ==========================================
    issue_series = (
        ml_df['Issue']
        if 'Issue' in ml_df.columns
        else pd.Series([1] * len(ml_df))
    )

    issue_text = issue_series.astype(str)

    ml_df['Issue_Num'] = (
        issue_text
        .str.extract(r'(\d+)')[0]
        .fillna(-1)
        .astype(int)
    )

    price_series = (
        ml_df['Price']
        if 'Price' in ml_df.columns
        else pd.Series([0.0] * len(ml_df))
    )

    ml_df['Price_Num'] = (
        pd.to_numeric(price_series, errors='coerce')
        .fillna(0.0)
    )

    if 'Unit Sales' in ml_df.columns:
        sales_series = ml_df['Unit Sales']
    elif 'sales' in ml_df.columns:
        sales_series = ml_df['sales']
    else:
        sales_series = pd.Series([0] * len(ml_df))

    ml_df['Sales_Num'] = (
        pd.to_numeric(sales_series, errors='coerce')
        .fillna(0)
    )

    rating_series = (
        ml_df['Rating']
        if 'Rating' in ml_df.columns
        else pd.Series(dtype=float)
    )

    rating_median = (
        pd.to_numeric(rating_series, errors='coerce')
        .median()
    )

    ml_df['Rating_Num'] = (
        pd.to_numeric(rating_series, errors='coerce')
        .fillna(
            rating_median if not pd.isna(rating_median) else 3.0
        )
    )

    # ==========================================
    # 2. Release Year 动态兼容
    # ==========================================
    year_col = next(
        (
            c for c in [
                'Release Year',
                'Release_Year',
                'Year',
                'release_year'
            ]
            if c in ml_df.columns
        ),
        None
    )

    year_series = (
        ml_df[year_col]
        if year_col
        else pd.Series([2026] * len(ml_df))
    )

    ml_df['Year_Num'] = (
        pd.to_numeric(year_series, errors='coerce')
        .fillna(2026)
        .astype(int)
    )

    # ==========================================
    # 3. 安全因子化
    # ==========================================
    def safe_factorize(column_candidates):

        col = next(
            (c for c in column_candidates if c in ml_df.columns),
            None
        )

        if col:
            series = ml_df[col]
        else:
            series = pd.Series(
                ['Unknown'] * len(ml_df),
                dtype='object'
            )

        return pd.factorize(
            series.fillna('Unknown')
        )[0]

    ml_df['Publisher_Code'] = safe_factorize([
        'Studio/Pub',
        'Publisher',
        'publisher',
        'Studio',
        'Pub'
    ])

    ml_df['ComicType_Code'] = safe_factorize([
        'Comic_Type',
        'comic_type',
        'Comic Type'
    ])

    # ==========================================
    # 4. 特征矩阵
    # ==========================================
    features = [
        'Sales_Num',
        'Issue_Num',
        'Price_Num',
        'Rating_Num',
        'Publisher_Code',
        'Year_Num',
        'ComicType_Code'
    ]

    X = StandardScaler().fit_transform(
        ml_df[features]
    )

    # ==========================================
    # 5. 小样本保护
    # ==========================================
    n_clusters = min(4, len(ml_df))

    if n_clusters < 2:

        ml_df['Cluster'] = 0
        ml_df['Cluster_Label'] = "Unknown"

        ml_df['Silhouette_Score'] = 0.0

        ml_df['PCA1'] = 0.0
        ml_df['PCA2'] = 0.0

        ml_df['PCA_Explained_Variance'] = 0.0

        return ml_df

    # ==========================================
    # 6. KMeans
    # ==========================================
    kmeans = KMeans(
        n_clusters=n_clusters,
        init='k-means++',
        n_init=20,
        max_iter=500,
        random_state=42
    )

    ml_df['Cluster'] = kmeans.fit_predict(X)

    # ==========================================
    # 7. Silhouette Score
    # ==========================================
    unique_cluster_num = ml_df['Cluster'].nunique()

    if unique_cluster_num > 1:
        sil_score = silhouette_score(
            X,
            ml_df['Cluster']
        )
    else:
        sil_score = 0.0

    ml_df['Silhouette_Score'] = sil_score

    # ==========================================
    # 8. PCA
    # ==========================================
    n_components = min(
        2,
        len(ml_df),
        X.shape[1]
    )

    pca = PCA(
        n_components=n_components,
        random_state=42
    )

    pca_result = pca.fit_transform(X)

    ml_df['PCA1'] = pca_result[:, 0]

    if n_components > 1:
        ml_df['PCA2'] = pca_result[:, 1]
    else:
        ml_df['PCA2'] = 0.0

    ml_df['PCA_Explained_Variance'] = (
        pca.explained_variance_ratio_.sum()
    )

    # ==========================================
    # 9. 商业语义映射
    # ==========================================
    cluster_stats = (
        ml_df
        .groupby('Cluster')['Sales_Num']
        .mean()
        .sort_values(ascending=False)
    )

    ranked_clusters = cluster_stats.index.tolist()

    labels = [
        "Blockbuster IP (大IP主线)",
        "Event Comics (独立大事件)",
        "Premium Series (精品限定)",
        "Long Tail (长尾市场)"
    ]

    mapping = {
        cluster: labels[i]
        for i, cluster in enumerate(ranked_clusters)
    }

    ml_df['Cluster_Label'] = (
        ml_df['Cluster']
        .map(mapping)
    )

    return ml_df