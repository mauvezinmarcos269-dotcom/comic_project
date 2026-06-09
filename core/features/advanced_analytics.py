import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from collections import Counter
import re

def perform_pca_clustering(df, n_clusters=3):
    features = ["Unit Sales", "Price", "Release Year"]
    analysis_df = df[features].dropna().copy()
    if len(analysis_df) < max(10, n_clusters): return None
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(analysis_df)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    analysis_df['Cluster'] = kmeans.fit_predict(scaled_data)
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    analysis_df['PCA1'] = pca_result[:, 0]
    analysis_df['PCA2'] = pca_result[:, 1]
    analysis_df['Title'] = df.loc[analysis_df.index, 'Title']
    analysis_df['Studio/Pub'] = df.loc[analysis_df.index, 'Studio/Pub']
    return analysis_df

def extract_title_keywords(df, top_n=20):
    # 如果没有 Norm_Title，自动回退使用原始 Title 列
    target_col = "Norm_Title" if "Norm_Title" in df.columns else "Title"
    
    if target_col not in df.columns or df.empty:
        return pd.DataFrame(columns=["Word", "Frequency"])

    stop_words = {"the", "a", "of", "and", "in", "to", "for", "vs", "vol", "issue", "comic", "comics", "is"}
    all_words = []
    
    for title in df[target_col].dropna():
        # 使用正则直接提取长度 >= 3 的连续纯字母单词
        words = re.findall(r'\b[a-zA-Z]{3,}\b', str(title).lower())
        all_words.extend([w for w in words if w not in stop_words])
                
    word_counts = Counter(all_words).most_common(top_n)
    return pd.DataFrame(word_counts, columns=["Word", "Frequency"])

def perform_regression(df):
    analysis_df = df[["Price", "Unit Sales"]].dropna()
    analysis_df = analysis_df[analysis_df["Price"] > 0]
    if len(analysis_df) < 5: return None, None
    X = sm.add_constant(analysis_df["Price"])
    y = analysis_df["Unit Sales"]
    model = sm.OLS(y, X).fit()
    analysis_df['Predicted_Sales'] = model.predict(X)
    return analysis_df, str(model.summary())

def get_special_decade_ranking(df, start=2010, end=2019):
    subset = df[(df["Release Year"] >= start) & (df["Release Year"] <= end)]
    title_col = "Norm_Title" if "Norm_Title" in subset.columns else "Title"
    ranking = subset.groupby(title_col)["Unit Sales"].sum().sort_values(ascending=False).head(10)
    
    target_series = ["star wars", "detective comics", "amazing spider-man"]
    special_notes = []
    for title, sales in ranking.items():
        if any(ts in str(title).lower() for ts in target_series):
            special_notes.append((title, sales))
    return ranking, special_notes
