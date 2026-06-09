import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.advanced_analytics import get_special_decade_ranking

def plot_publisher_share(df):
    share = df.groupby("Studio/Pub")["Unit Sales"].sum().sort_values(ascending=False)
    top_5 = share.head(5)
    others = pd.Series({"Others": share.iloc[5:].sum()}) if len(share) > 5 else pd.Series(dtype=float)
        
    final_share = pd.concat([top_5, others]).reset_index()
    final_share.columns = ["Publisher", "Sales"]
    
    fig = px.pie(final_share, values='Sales', names='Publisher', hole=0.4,
                 title="出版商市场销量份额占比", color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_marvel_vs_dc_trend(df):
    sub_df = df[df["Studio/Pub"].str.lower().isin(["marvel", "dc"])].copy()
    sub_df = sub_df[sub_df["Release Year"] > 1980]
    trend = sub_df.groupby(["Release Year", "Studio/Pub"])["Unit Sales"].sum().reset_index()
    
    fig = px.line(trend, x="Release Year", y="Unit Sales", color="Studio/Pub",
                  title="Marvel 与 DC 年度总销量对比",
                  color_discrete_map={"Marvel": "#E23636", "DC": "#0476F2"}, 
                  markers=True)
    return fig

def plot_top_creators(df, role="Writer", top_n=15):
    if role not in df.columns: return None
    invalid_labels = {"not available", "not enriched", "unknown", "none", "nan", ""}
    
    sub_df = df[[role, "Unit Sales"]].dropna().copy()
    sub_df[role] = sub_df[role].astype(str).str.strip()
    sub_df = sub_df[~sub_df[role].str.lower().isin(invalid_labels)]
    
    sub_df[role] = sub_df[role].str.replace(" / ", ", ").str.replace(";", ", ").str.split(", ")
    exploded_df = sub_df.explode(role)
    exploded_df[role] = exploded_df[role].str.strip()
    exploded_df = exploded_df[~exploded_df[role].str.lower().isin(invalid_labels) & (exploded_df[role] != "")]
    
    creator_sales = exploded_df.groupby(role)["Unit Sales"].sum().reset_index()
    top_data = creator_sales.sort_values(by="Unit Sales", ascending=False).head(top_n)
    if top_data.empty: return None
        
    role_label = "编剧" if role == "Writer" else "画师"

    fig = px.bar(top_data, x="Unit Sales", y=role, orientation='h',
                 title=f"销量 Top {top_n} {role_label}", labels={"Unit Sales": "总销量(册)", role: role_label},
                 color="Unit Sales", color_continuous_scale="Viridis")
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    return fig

def plot_time_series_trend(df):
    trend = df.groupby("Release Year")["Unit Sales"].sum().reset_index()
    trend = trend[trend["Release Year"] > 1930]
    trend['Rolling'] = trend['Unit Sales'].rolling(3).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["Release Year"], y=trend["Unit Sales"], name='年度总销量'))
    fig.add_trace(go.Scatter(x=trend["Release Year"], y=trend['Rolling'], name='3年均线', line=dict(dash='dash')))
    fig.update_layout(title="行业总体销量时间序列")
    return fig

def plot_correlation_heatmap(df, method='spearman'):
    numeric_cols = ["Unit Sales", "Price", "Release Year", "Rating", "Page Count"]
    valid_cols = [c for c in numeric_cols if c in df.columns and not df[c].isna().all()]
    df_num = df[valid_cols].replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(df_num) < 3 or len(valid_cols) < 2: return None
    corr = df_num.corr(method=method)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="Blues", aspect="auto", title=f"特征相关性矩阵 ({method})")
    return fig

def plot_rating_vs_sales(df):
    if "Rating" not in df.columns or df["Rating"].isna().all(): return None
    plot_df = df.dropna(subset=["Rating", "Unit Sales"]).copy()
    fig = px.scatter(plot_df, x="Rating", y="Unit Sales", color="Studio/Pub", hover_name="Title",
                     title="评分与销量分布", opacity=0.7)
    return fig

def plot_pca_clusters(pca_df):
    pca_df['Cluster'] = pca_df['Cluster'].astype(str)
    return px.scatter(pca_df, x="PCA1", y="PCA2", color="Cluster", hover_data=["Title", "Unit Sales"], title="PCA 聚类分布")

def plot_word_freq(word_df):
    fig = px.bar(word_df, x="Frequency", y="Word", orientation='h', title="标题高频词汇")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def plot_decade_top10(df, start=2010, end=2019):
    ranking, _ = get_special_decade_ranking(df, start, end)
    top_df = ranking.reset_index()
    top_df.columns = ["Title", "Unit Sales"]
    return px.bar(top_df, x="Title", y="Unit Sales", text="Unit Sales", title=f"{start}-{end} 漫画系列总销量 Top10")