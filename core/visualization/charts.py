import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.advanced_analytics import get_special_decade_ranking
from core.constants import YEAR_COLUMN_CANDIDATES


def _get_year_col(df: pd.DataFrame) -> str | None:
    """从候选列表中找到第一个存在于 df 的年份列名，找不到返回 None。"""
    return next((c for c in YEAR_COLUMN_CANDIDATES if c in df.columns), None)


def _get_pub_col(df: pd.DataFrame) -> str | None:
    """动态获取出版商列名"""
    return next((c for c in ["Studio/Pub", "Publisher", "publisher", "Studio", "Pub"] if c in df.columns), None)


def _get_sales_col(df: pd.DataFrame) -> str | None:
    """动态获取销量列名"""
    return next((c for c in ["Unit Sales", "sales", "Sales"] if c in df.columns), None)


def plot_publisher_share(df: pd.DataFrame):
    pub_col = _get_pub_col(df)
    sales_col = _get_sales_col(df)
    
    if not pub_col or not sales_col:
        return None
        
    share = df.groupby(pub_col)[sales_col].sum().sort_values(ascending=False)
    top_5 = share.head(5)
    others = (
        pd.Series({"Others": share.iloc[5:].sum()})
        if len(share) > 5
        else pd.Series(dtype=float)
    )
    final_share = pd.concat([top_5, others]).reset_index()
    final_share.columns = ["Publisher", "Sales"]

    fig = px.pie(
        final_share, values="Sales", names="Publisher", hole=0.4,
        title="出版商市场销量份额占比",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def plot_marvel_vs_dc_trend(df: pd.DataFrame):
    pub_col = _get_pub_col(df)
    sales_col = _get_sales_col(df)
    year_col = _get_year_col(df)
    
    if not pub_col or not sales_col or not year_col:
        return None

    sub_df = df[df[pub_col].str.lower().isin(["marvel", "dc"])].copy()
    sub_df = sub_df[pd.to_numeric(sub_df[year_col], errors="coerce").fillna(0) > 1980]
    trend = (
        sub_df.groupby([year_col, pub_col])[sales_col]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend, x=year_col, y=sales_col, color=pub_col,
        title="Marvel 与 DC 年度总销量对比",
        color_discrete_map={"Marvel": "#E23636", "DC": "#0476F2"},
        markers=True,
    )
    fig.update_layout(xaxis_title="发行年份")
    return fig


def plot_top_creators(df: pd.DataFrame, role: str = "Writer", top_n: int = 15):
    sales_col = _get_sales_col(df)
    
    if role not in df.columns or not sales_col:
        return None
        
    invalid_labels = {"not available", "not enriched", "unknown", "none", "nan", ""}

    sub_df = df[[role, sales_col]].dropna().copy()
    sub_df[role] = sub_df[role].astype(str).str.strip()
    sub_df = sub_df[~sub_df[role].str.lower().isin(invalid_labels)]

    sub_df[role] = (
        sub_df[role]
        .str.replace(" / ", ", ", regex=False)
        .str.replace(";", ", ", regex=False)
        .str.split(", ")
    )
    exploded_df = sub_df.explode(role)
    exploded_df[role] = exploded_df[role].str.strip()
    exploded_df = exploded_df[
        ~exploded_df[role].str.lower().isin(invalid_labels)
        & (exploded_df[role] != "")
    ]

    creator_sales = exploded_df.groupby(role)[sales_col].sum().reset_index()
    top_data = creator_sales.sort_values(by=sales_col, ascending=False).head(top_n)
    if top_data.empty:
        return None

    role_label = "编剧" if role == "Writer" else "画师"
    fig = px.bar(
        top_data, x=sales_col, y=role, orientation="h",
        title=f"销量 Top {top_n} {role_label}",
        labels={sales_col: "总销量(册)", role: role_label},
        color=sales_col, color_continuous_scale="Viridis",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
    return fig


def plot_time_series_trend(df: pd.DataFrame):
    year_col = _get_year_col(df)
    sales_col = _get_sales_col(df)
    
    if not year_col or not sales_col:
        return None

    trend = df.groupby(year_col)[sales_col].sum().reset_index()
    trend = trend[pd.to_numeric(trend[year_col], errors="coerce").fillna(0) > 1930]
    trend["Rolling"] = trend[sales_col].rolling(3).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend[year_col], y=trend[sales_col], name="年度总销量"))
    fig.add_trace(
        go.Scatter(
            x=trend[year_col], y=trend["Rolling"],
            name="3年均线", line=dict(dash="dash"),
        )
    )
    fig.update_layout(title="行业总体销量时间序列", xaxis_title="发行年份")
    return fig


def plot_correlation_heatmap(df: pd.DataFrame, method: str = "spearman"):
    year_col = _get_year_col(df)
    sales_col = _get_sales_col(df)
    
    base_cols = [c for c in [sales_col, "Price", "Rating", "Page Count"] if c]
    numeric_cols = base_cols + ([year_col] if year_col else [])

    valid_cols = [c for c in numeric_cols if c in df.columns and not df[c].isna().all()]
    df_num = df[valid_cols].replace([np.inf, -np.inf], np.nan).dropna()

    if len(df_num) < 3 or len(valid_cols) < 2:
        return None
    corr = df_num.corr(method=method)
    fig = px.imshow(
        corr, text_auto=True, color_continuous_scale="Blues",
        aspect="auto", title=f"特征相关性矩阵 ({method})",
    )
    return fig


def plot_rating_vs_sales(df: pd.DataFrame):
    sales_col = _get_sales_col(df)
    
    if "Rating" not in df.columns or df["Rating"].isna().all() or not sales_col:
        return None
        
    plot_df = df.dropna(subset=["Rating", sales_col]).copy()
    pub_col = _get_pub_col(df)
    color_col = pub_col if pub_col else None
    
    hover_col = next((c for c in ["Title", "Norm_Title"] if c in df.columns), None)
    
    fig = px.scatter(
        plot_df, x="Rating", y=sales_col,
        color=color_col, hover_name=hover_col,
        title="评分与销量分布", opacity=0.7,
    )
    return fig


def plot_pca_clusters(pca_df: pd.DataFrame):
    pca_df = pca_df.copy()
    pca_df["Cluster"] = pca_df["Cluster"].astype(str)
    
    sales_col = _get_sales_col(pca_df)
    hover_cols = [c for c in ["Title", "Norm_Title", sales_col] if c and c in pca_df.columns]
    
    return px.scatter(
        pca_df, x="PCA1", y="PCA2", color="Cluster",
        hover_data=hover_cols, title="PCA 聚类分布",
    )


def plot_word_freq(word_df: pd.DataFrame):
    if word_df.empty:
        return None
    fig = px.bar(word_df, x="Frequency", y="Word", orientation="h", title="标题高频词汇")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def plot_decade_top10(df: pd.DataFrame, start: int = 2010, end: int = 2019):
    ranking, _ = get_special_decade_ranking(df, start, end)
    if ranking.empty:
        return None
    top_df = ranking.reset_index()
    # 强制将内部名称对齐到 Unit Sales 用于通用图表构建
    top_df.columns = ["Title", "Unit Sales"]
    return px.bar(
        top_df, x="Title", y="Unit Sales", text="Unit Sales",
        title=f"{start}-{end} 漫画系列总销量 Top10",
    )