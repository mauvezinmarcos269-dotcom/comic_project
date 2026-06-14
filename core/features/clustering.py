import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def perform_advanced_clustering(df):
    ml_df = df.copy()

    # 1. 基础数值清洗
    ml_df['Issue_Num'] = ml_df['Issue'].astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)
    ml_df['Price_Num'] = pd.to_numeric(ml_df['Price'], errors='coerce').fillna(0.0)
    ml_df['Sales_Num'] = pd.to_numeric(ml_df.get('Unit Sales', ml_df.get('sales', 0)), errors='coerce').fillna(0)
    
    rating_median = pd.to_numeric(ml_df.get('Rating', pd.Series(dtype=float)), errors='coerce').median()
    ml_df['Rating_Num'] = pd.to_numeric(ml_df.get('Rating', pd.Series(dtype=float)), errors='coerce').fillna(rating_median if not pd.isna(rating_median) else 3.0)

    # 2. 增加 dtype='object' 消除 FutureWarning
    def safe_factorize(col_name):
        series = ml_df[col_name] if col_name in ml_df.columns else pd.Series(['Unknown'] * len(ml_df), dtype='object')
        return pd.factorize(series.fillna('Unknown'))[0]

    ml_df['Publisher_Code'] = safe_factorize('Studio/Pub')
    ml_df['Year_Num'] = pd.to_numeric(ml_df.get('Release Year', 2026), errors='coerce').fillna(2026).astype(int)
    ml_df['ComicType_Code'] = safe_factorize('Comic_Type')

    features = ['Sales_Num', 'Issue_Num', 'Price_Num', 'Rating_Num', 'Publisher_Code', 'Year_Num', 'ComicType_Code']
    X = StandardScaler().fit_transform(ml_df[features])

    # 3. 锁死 K=4，仅计算 Silhouette Score而不进行过度调参
    kmeans = KMeans(n_clusters=4, init='k-means++', n_init=20, max_iter=500, random_state=42)
    ml_df['Cluster'] = kmeans.fit_predict(X)
    ml_df['Silhouette_Score'] = silhouette_score(X, ml_df['Cluster'])

    # 4. 执行 PCA 降维并计算方差贡献率
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X)
    ml_df['PCA1'], ml_df['PCA2'] = pca_result[:, 0], pca_result[:, 1]
    ml_df['PCA_Explained_Variance'] = pca.explained_variance_ratio_.sum()

    # 5. 动态业务语义映射 (按平均销量从高到低严格绑定商业逻辑)
    cluster_stats = ml_df.groupby('Cluster')['Sales_Num'].mean().sort_values(ascending=False)
    ranked = cluster_stats.index.tolist()
    
    mapping = {
        ranked[0]: "Blockbuster IP (大IP主线)",
        ranked[1]: "Event Comics (独立大事件)",
        ranked[2]: "Premium Series (精品限定)",
        ranked[3]: "Long Tail (长尾市场)"
    }
    ml_df['Cluster_Label'] = ml_df['Cluster'].map(mapping)
    return ml_df