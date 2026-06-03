import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.advanced_analytics import get_special_decade_ranking

def plot_publisher_share(df):
    """出版商市场份额占比饼图"""
    share = df.groupby("Studio/Pub")["Unit Sales"].sum().sort_values(ascending=False)
    top_5 = share.head(5)
    
    if len(share) > 5:
        others = pd.Series({"Others": share.iloc[5:].sum()})
    else:
        others = pd.Series(dtype=float)
        
    final_share = pd.concat([top_5, others]).reset_index()
    final_share.columns = ["Publisher", "Sales"]
    
    fig = px.pie(final_share, values='Sales', names='Publisher', hole=0.4,
                 title="行业市场份额占比 (销量维度)",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_marvel_vs_dc_trend(df):
    """漫威与 DC 年度销量趋势大对决"""
    sub_df = df[df["Studio/Pub"].str.lower().isin(["marvel", "dc"])].copy()
    sub_df = sub_df[sub_df["Release Year"] > 1980]
    
    trend = sub_df.groupby(["Release Year", "Studio/Pub"])["Unit Sales"].sum().reset_index()
    fig = px.line(trend, x="Release Year", y="Unit Sales", color="Studio/Pub",
                  title="Marvel vs DC 现代纪元年度总销量对决",
                  color_discrete_map={"Marvel": "crimson", "DC": "royalblue"},
                  markers=True)
    return fig

def plot_rating_vs_sales(df):
    """评分与销量散点关联图（保留作为安全降级）"""
    if "Rating" not in df.columns or df["Rating"].isna().all():
        return None
        
    plot_df = df.dropna(subset=["Rating", "Unit Sales"]).copy()
    fig = px.scatter(plot_df, x="Rating", y="Unit Sales", color="Studio/Pub", hover_name="Title",
                     title="口碑与商业价值：评分-销量散点分布", opacity=0.7)
    return fig

def plot_top_creators(df, role="Writer", top_n=20):
    """
    高级数据挖掘：分析总销量前 N 名的核心创作者
    支持对多位联合创作者进行 '.explode()' 向量化拆分，体现高级 Pandas 技巧
    """
    if role not in df.columns:
        return None
        
    # 定义过滤非有效富化数据的清洗垃圾集
    invalid_labels = {"not available", "not enriched (待执行管线富化)", "unknown", "none", "nan", ""}
    
    # 提取所需列并清洗
    sub_df = df[[role, "Unit Sales"]].dropna().copy()
    sub_df[role] = sub_df[role].astype(str).str.strip()
    
    # 过滤掉完全无效的初始行
    sub_df = sub_df[~sub_df[role].str.lower().isin(invalid_labels)]
    
    # 【核心技巧】：兼容联名创作。将 "Dan Slott / Christos Gage" 或 "Dan Slott, Christos Gage" 统一切割为列表
    sub_df[role] = sub_df[role].str.replace(" / ", ", ").str.replace(";", ", ")
    sub_df[role] = sub_df[role].str.split(", ")
    
    # 展开列表，将多创作者切分为多行，从而精准统计个人独立贡献的总销量
    exploded_df = sub_df.explode(role)
    exploded_df[role] = exploded_df[role].str.strip()
    
    # 再次过滤清洗拆分后可能产生的空白或无效名
    exploded_df = exploded_df[~exploded_df[role].str.lower().isin(invalid_labels) & (exploded_df[role] != "")]
    
    # 分组聚合总销量
    creator_sales = exploded_df.groupby(role)["Unit Sales"].sum().reset_index()
    top_data = creator_sales.sort_values(by="Unit Sales", ascending=False).head(top_n)
    
    if top_data.empty:
        return None
        
    role_label = "编剧 (Writer)" if role == "Writer" else "画师 (Artist)"
    
    fig = px.bar(top_data, x="Unit Sales", y=role, orientation='h',
                 title=f"美漫工业金牌核心：总销量 Top {top_n} 顶尖{role_label}排行",
                 labels={"Unit Sales": "联合承载总销量 (册)", role: role_label},
                 color="Unit Sales", color_continuous_scale="Blugrn")
    
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=550)
    return fig

def plot_correlation_heatmap(df, method='spearman'):
    """数值特征相关性矩阵"""
    numeric_cols = ["Unit Sales", "Price", "Release Year", "Rating", "Page Count"]
    valid_cols = [c for c in numeric_cols if c in df.columns and not df[c].isna().all()]
    df_num = df[valid_cols].replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(df_num) < 3 or len(valid_cols) < 2: return None
        
    corr = df_num.corr(method=method)
    
    # 修正 Pylance 静态类型报错，解耦 text_auto 传参
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", 
                    aspect="auto", title=f"数值特征相关性矩阵 ({method})")
    fig.update_traces(texttemplate="%{z:.2f}")
    return fig

def plot_time_series_trend(df):
    trend = df.groupby("Release Year")["Unit Sales"].sum().reset_index()
    trend = trend[trend["Release Year"] > 1930]
    trend['Rolling'] = trend['Unit Sales'].rolling(3).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["Release Year"], y=trend["Unit Sales"], name='年度总销量'))
    fig.add_trace(go.Scatter(x=trend["Release Year"], y=trend['Rolling'], name='3年均线', line=dict(dash='dash')))
    fig.update_layout(title="行业大盘时间序列")
    return fig

def plot_pca_clusters(pca_df):
    pca_df['Cluster'] = pca_df['Cluster'].astype(str)
    return px.scatter(pca_df, x="PCA1", y="PCA2", color="Cluster",
                      hover_data=["Title", "Unit Sales", "Price"], title="K-Means 聚类投影")

def plot_word_freq(word_df):
    fig = px.bar(word_df, x="Frequency", y="Word", orientation='h', title="高频词汇挖掘")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def plot_decade_top10(df, start=2010, end=2019):
    ranking, notes = get_special_decade_ranking(df, start, end)
    top_df = ranking.reset_index()
    top_df.columns = ["Title", "Unit Sales"]
    return px.bar(top_df, x="Title", y="Unit Sales", text="Unit Sales", title=f"{start}-{end} 销量 Top10")