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
    if len(analysis_df) < 10:
        return None
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

def perform_regression(df):
    analysis_df = df[["Price", "Unit Sales"]].dropna()
    analysis_df = analysis_df[analysis_df["Price"] > 0]
    if len(analysis_df) < 5:
        return None, None
    X = sm.add_constant(analysis_df["Price"])
    y = analysis_df["Unit Sales"]
    model = sm.OLS(y, X).fit()
    analysis_df['Predicted_Sales'] = model.predict(X)
    return analysis_df, model.summary()

def extract_title_keywords(df, top_n=20):
    stopwords = {"the", "of", "and", "a", "to", "in", "is", "vol", "issue", "comic", "comics", "for"}
    all_words = []
    for title in df["Title"].dropna():
        words = re.findall(r'\b[a-zA-Z]{3,}\b', str(title).lower())
        all_words.extend([w for w in words if w not in stopwords])
    return pd.DataFrame(Counter(all_words).most_common(top_n), columns=['Word', 'Frequency'])

def get_special_decade_ranking(df, start=2010, end=2019):
    subset = df[(df["Release Year"] >= start) & (df["Release Year"] <= end)]
    ranking = subset.groupby("Title")["Unit Sales"].sum().sort_values(ascending=False).head(10)
    target_series = ["star wars", "detective comics", "amazing spider-man"]
    special_notes = []
    for title, sales in ranking.items():
        if any(ts in title.lower() for ts in target_series):
            special_notes.append((title, sales))
    return ranking, special_notes

