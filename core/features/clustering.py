import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def perform_advanced_clustering(df):
    ml_df = df.copy()

    # 1. 极度安全的数值提取
    issue_series = ml_df['Issue'] if 'Issue' in ml_df.columns else pd.Series([1]*len(ml_df))
    ml_df['Issue_Num'] = issue_series.astype(str).str.extract(r'(\d+)')[0].fillna(0).astype(int)

    price_series = ml_df['Price'] if 'Price' in ml_df.columns else pd.Series([0.0]*len(ml_df))
    ml_df['Price_Num'] = pd.to_numeric(price_series, errors='coerce').fillna(0.0)

    sales_series = ml_df['Unit Sales'] if 'Unit Sales' in ml_df.columns else ml_df['sales'] if 'sales' in ml_df.columns else pd.Series([0]*len(ml_df))
    ml_df['Sales_Num'] = pd.to_numeric(sales_series, errors='coerce').fillna(0)
    
    rating_series = ml_df['Rating'] if 'Rating' in ml_df.columns else pd.Series(dtype=float)
    rating_median = pd.to_numeric(rating_series, errors='coerce').median()
    ml_df['Rating_Num'] = pd.to_numeric(rating_series, errors='coerce').fillna(rating_median if not pd.isna(rating_median) else 3.0)

    # 2. 动态列名解耦：Release Year 多变体兼容
    year_col = next((c for c in ['Release Year', 'Release_Year', 'Year', 'release_year'] if c in ml_df.columns), None)
    year_series = ml_df[year_col] if year_col else pd.Series([2026]*len(ml_df))
    ml_df['Year_Num'] = pd.to_numeric(year_series, errors='coerce').fillna(2026).astype(int)

    # 3. 安全的因子化编码
    pub_col = 'Studio/Pub' if 'Studio/Pub' in ml_df.columns else 'Publisher' if 'Publisher' in ml_df.columns else 'publisher' if 'publisher' in ml_df.columns else None
    
    def safe_factorize(col_name):
        if col_name and col_name in ml_df.columns:
            series = ml_df[col_name]
        else:
            series = pd.Series(['Unknown'] * len(ml_df), dtype='object')
        return pd.factorize(series.fillna('Unknown'))[0]

    ml_df['Publisher_Code'] = safe_factorize(pub_col)
    ml_df['ComicType_Code'] = safe_factorize('Comic_Type')

    # 4. 构建特征矩阵
    features = ['Sales_Num', 'Issue_Num', 'Price_Num', 'Rating_Num', 'Publisher_Code', 'Year_Num', 'ComicType_Code']
    X = StandardScaler().fit_transform(ml_df[features])

    # 5. 防崩设计：小样本自适应
    n_clusters = min(4, len(ml_df))
    if n_clusters < 2:
        ml_df['Cluster'] = 0
        ml_df['Cluster_Label'] = "Unknown"
        ml_df['Silhouette_Score'] = 0.0
        ml_df['PCA1'] = 0.0
        ml_df['PCA2'] = 0.0
        ml_df['PCA_Explained_Variance'] = 0.0
        return ml_df

    kmeans = KMeans(n_clusters=n_clusters, init='k-means++', n_init=20, max_iter=500, random_state=42)
    ml_df['Cluster'] = kmeans.fit_predict(X)
    
    try:
        ml_df['Silhouette_Score'] = silhouette_score(X, ml_df['Cluster'])
    except Exception:
        ml_df['Silhouette_Score'] = 0.0

    # 6. 执行 PCA 降维并计算方差贡献率
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X)
    ml_df['PCA1'], ml_df['PCA2'] = pca_result[:, 0], pca_result[:, 1]
    ml_df['PCA_Explained_Variance'] = pca.explained_variance_ratio_.sum()

    # 7. 动态且防越界的业务语义映射
    cluster_stats = ml_df.groupby('Cluster')['Sales_Num'].mean().sort_values(ascending=False)
    ranked = cluster_stats.index.tolist()
    
    labels = [
        "Blockbuster IP (大IP主线)",
        "Event Comics (独立大事件)",
        "Premium Series (精品限定)",
        "Long Tail (长尾市场)"
    ]
    
    mapping = {cluster: labels[i] for i, cluster in enumerate(ranked)}
    ml_df['Cluster_Label'] = ml_df['Cluster'].map(mapping)
    
    return ml_df