import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def perform_advanced_clustering(df):
    """
    全量数据的真实 ML 聚类管线
    """
    ml_df = df.copy()

    # 1. 基础数值清洗（提取纯数字，处理 NaN）
    ml_df['Issue_Num'] = ml_df['Issue'].astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)
    ml_df['Price_Num'] = pd.to_numeric(ml_df['Price'], errors='coerce').fillna(0.0)
    ml_df['Sales_Num'] = pd.to_numeric(ml_df.get('Unit Sales', ml_df.get('sales', 0)), errors='coerce').fillna(0)

    rating_median = pd.to_numeric(ml_df.get('Rating', pd.Series(dtype=float)), errors='coerce').median()
    ml_df['Rating_Num'] = pd.to_numeric(ml_df.get('Rating', pd.Series(dtype=float)), errors='coerce').fillna(
        rating_median if not pd.isna(rating_median) else 3.0)

    # 2. 增加高维特征编码 (Publisher, Year, Comic_Type)
    ml_df['Publisher_Code'] = pd.factorize(ml_df.get('Studio/Pub', 'Unknown').fillna('Unknown'))[0]
    ml_df['Year_Num'] = pd.to_numeric(ml_df.get('Release Year', 2026), errors='coerce').fillna(2026).astype(int)
    ml_df['ComicType_Code'] = pd.factorize(ml_df.get('Comic_Type', 'Unknown').fillna('Unknown'))[0]

    # 3. 构建特征矩阵
    features = ['Sales_Num', 'Issue_Num', 'Price_Num', 'Rating_Num', 'Publisher_Code', 'Year_Num', 'ComicType_Code']
    features = [f for f in features if f in ml_df.columns] # 容错检查
    X = ml_df[features]

    # 4. 标准化与 PCA (去除多余的 random_state)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X_scaled)
    ml_df['PCA1'] = pca_result[:, 0]
    ml_df['PCA2'] = pca_result[:, 1]

    # 5. 健壮的 KMeans 聚类
    kmeans = KMeans(n_clusters=4, init='k-means++', n_init=20, max_iter=500, random_state=42)
    ml_df['Cluster'] = kmeans.fit_predict(X_scaled)

    # 6. 计算轮廓系数 (Silhouette Score)
    try:
        sil_score = silhouette_score(X_scaled, ml_df['Cluster'])
    except:
        sil_score = 0.0
    ml_df['Silhouette_Score'] = sil_score

    # 7. 动态业务语义映射 (解决簇编号漂移的核心逻辑)
    # 按照每个簇的平均销量从高到低排序，动态赋予商业标签
    cluster_stats = ml_df.groupby('Cluster')['Sales_Num'].mean().sort_values(ascending=False)
    ranked_clusters = cluster_stats.index.tolist()

    # 强制安全映射：
    # 销量第1 -> 独立大事件 (峰值极高)
    # 销量第2 -> 大IP主线
    # 销量第3 -> 精品限定
    # 销量第4 -> 长尾市场
    mapping = {
        ranked_clusters[0]: "Event Comics (独立大事件)",
        ranked_clusters[1]: "Blockbuster IP (大IP主线)",
        ranked_clusters[2]: "Premium Series (精品限定)",
        ranked_clusters[3]: "Long Tail (长尾市场)"
    }
    
    ml_df['Cluster_Label'] = ml_df['Cluster'].map(mapping)
    return ml_df