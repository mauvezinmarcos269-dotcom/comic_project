import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def perform_advanced_clustering(df):
    ml_df = df.copy()

    # 1. 极度安全的数值提取 (防 KeyError 与 AttributeError)
    issue_series = ml_df['Issue'] if 'Issue' in ml_df.columns else pd.Series([1]*len(ml_df))
    ml_df['Issue_Num'] = issue_series.astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)

    price_series = ml_df['Price'] if 'Price' in ml_df.columns else pd.Series([0.0]*len(ml_df))
    ml_df['Price_Num'] = pd.to_numeric(price_series, errors='coerce').fillna(0.0)

    sales_series = ml_df['Unit Sales'] if 'Unit Sales' in ml_df.columns else ml_df['sales'] if 'sales' in ml_df.columns else pd.Series([0]*len(ml_df))
    ml_df['Sales_Num'] = pd.to_numeric(sales_series, errors='coerce').fillna(0)
    
    rating_series = ml_df['Rating'] if 'Rating' in ml_df.columns else pd.Series(dtype=float)
    rating_median = pd.to_numeric(rating_series, errors='coerce').median()
    ml_df['Rating_Num'] = pd.to_numeric(rating_series, errors='coerce').fillna(rating_median if not pd.isna(rating_median) else 3.0)

    # 2. 极度安全的因子化编码 (防多种列名与 DataFrame 切片错误)
    pub_col = 'Studio/Pub' if 'Studio/Pub' in ml_df.columns else 'Publisher' if 'Publisher' in ml_df.columns else 'publisher' if 'publisher' in ml_df.columns else None
    
    def safe_factorize(col_name):
        if col_name and col_name in ml_df.columns:
            series = ml_df[col_name]
        else:
            series = pd.Series(['Unknown'] * len(ml_df), dtype='object')
        return pd.factorize(series.fillna('Unknown'))[0]

    ml_df['Publisher_Code'] = safe_factorize(pub_col)
    ml_df['Year_Num'] = pd.to_numeric(ml_df.get('Release Year', 2026), errors='coerce').fillna(2026).astype(int)
    ml_df['ComicType_Code'] = safe_factorize('Comic_Type')

    # 3. 构建特征矩阵
    features = ['Sales_Num', 'Issue_Num', 'Price_Num', 'Rating_Num', 'Publisher_Code', 'Year_Num', 'ComicType_Code']
    X = StandardScaler().fit_transform(ml_df[features])

    # 4. 锁死 K=4 保持业务与答辩一致性，仅计算轮廓系数备用
    kmeans = KMeans(n_clusters=4, init='k-means++', n_init=20, max_iter=500, random_state=42)
    ml_df['Cluster'] = kmeans.fit_predict(X)
    ml_df['Silhouette_Score'] = silhouette_score(X, ml_df['Cluster'])

    # 5. 执行 PCA 降维并计算方差贡献率
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X)
    ml_df['PCA1'], ml_df['PCA2'] = pca_result[:, 0], pca_result[:, 1]
    ml_df['PCA_Explained_Variance'] = pca.explained_variance_ratio_.sum()

    # 6. 动态且稳定的业务语义映射
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