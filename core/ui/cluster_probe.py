import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# 全局固定色系，规避数据缺失导致的色带次序漂移
_CLUSTER_COLORS: dict[str, str] = {
    "Blockbuster IP (大IP主线)":   "#1f77b4",
    "Event Comics (独立大事件)":    "#d62728",
    "Premium Series (精品限定)":    "#2ca02c",
    "Long Tail (长尾市场)":         "#ff7f0e",
}

_LABEL_ORDER = list(_CLUSTER_COLORS.keys())

_CLUSTER_DESC: dict[str, str] = {
    _LABEL_ORDER[0]: "持续高销量，极长的日常连载周数与历史积累",
    _LABEL_ORDER[1]: "单期销量极端爆发突破常规，普遍集中在 #1 创刊号或年度联动节点",
    _LABEL_ORDER[2]: "发行长度受限，内容评分中位数极高，具备更强的精品艺术属性与客单价",
    _LABEL_ORDER[3]: "单刊日常销量处于中下游，但作品基数极其庞大，构成产业的基本长尾盘",
}


def _get_top_titles(df: pd.DataFrame, label: str, n: int = 3) -> str:
    """返回指定簇销量最高的 n 部作品标题，以顿号拼接。"""
    sub = df[df["Cluster_Label"] == label]
    if sub.empty:
        return "暂无数据"
    t_col = "Title" if "Title" in sub.columns else "Norm_Title" if "Norm_Title" in sub.columns else None
    if t_col is None:
        return "数据源缺失标题字段"
    titles = sub.nlargest(n, "Sales_Num")[t_col].dropna().unique().tolist()
    return "、".join(titles) if titles else "暂无代表作"


def _build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """计算各簇核心指标均值，用于热力图与雷达图。"""
    return df.groupby("Cluster_Label").agg(
        Sales_Num=("Sales_Num", "mean"),
        Price_Num=("Price_Num", "mean"),
        Rating_Num=("Rating_Num", "mean"),
        Issue_Num=("Issue_Num", "mean"),
    ).round(2)


def render_cluster_probe(probe_df: pd.DataFrame) -> None:
    """
    聚类多维探针主入口。
    接收已携带 ML 标签的切片视图 DataFrame（由全局数据筛选而来）。
    """
    probe_df = probe_df.copy()  # 深拷贝，杜绝 SettingWithCopyWarning

    st.markdown("### 🧠 智能聚类分析中心")

    # ── 模型元数据指标卡 ──────────────────────────────────────────────────────
    sil_score = probe_df["Silhouette_Score"].iloc[0] if "Silhouette_Score" in probe_df.columns else 0.0
    var_sum   = (probe_df["PCA_Explained_Variance"].iloc[0] * 100
                 if "PCA_Explained_Variance" in probe_df.columns else 0.0)

    col_m1, col_m2 = st.columns(2)
    col_m1.metric(
        "模型轮廓系数 (Silhouette)", f"{sil_score:.3f}",
        help="越接近 1 说明簇分离度与内聚度越好。"
    )
    col_m2.metric(
        "PCA 特征方差解释率", f"{var_sum:.1f}%",
        help="前两个主成分对原始 7 维特征空间信息的覆盖度。"
    )
    st.divider()

    tab_a, tab_b = st.tabs(["📊 统计与分布画像", "🔍 空间降维散点图"])

    # ── Tab A：统计画像 ────────────────────────────────────────────────────────
    with tab_a:
        summary = _build_summary(probe_df)
        col_t1, col_t2 = st.columns([1, 1])

        with col_t1:
            st.markdown("#### 📊 聚类群组统计特性中心")
            st.dataframe(summary, use_container_width=True)

            st.markdown("#### 📈 聚类群组规模分布 (长尾效应量化验证)")
            cluster_counts = (
                probe_df["Cluster_Label"]
                .value_counts()
                .reset_index()
                .rename(columns={"Cluster_Label": "Cluster", "count": "Count"})
            )
            fig_bar = px.bar(
                cluster_counts, x="Cluster", y="Count",
                color="Cluster", text="Count",
                color_discrete_map=_CLUSTER_COLORS,
            )
            fig_bar.update_layout(
                showlegend=False,
                xaxis_title="聚类群体", yaxis_title="作品样本期数",
                height=320, margin=dict(b=0, t=30),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_t2:
            st.markdown("#### 🎯 核心特征聚类中心热力图")
            # MinMaxScaler 归一化，解决量纲差异导致的色彩压制
            summary_norm = pd.DataFrame(
                MinMaxScaler().fit_transform(summary),
                columns=summary.columns,
                index=summary.index,
            )
            fig_heat = px.imshow(
                summary_norm, text_auto=True, aspect="auto",
                color_continuous_scale="RdBu_r",
                labels=dict(x="特征维度", y="聚类群体", color="归一化强度"),
            )
            fig_heat.update_traces(texttemplate="%{z:.2f}")
            fig_heat.update_xaxes(side="top")
            fig_heat.update_layout(height=300, margin=dict(t=50, b=10))
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("#### 🕸️ 聚类中心多维雷达图")
            fig_radar = go.Figure()
            for label in summary_norm.index:
                data = summary_norm.loc[label]
                fig_radar.add_trace(go.Scatterpolar(
                    r=[data["Sales_Num"], data["Price_Num"],
                       data["Rating_Num"], data["Issue_Num"]],
                    theta=["销量特征", "定价策略", "内容评分", "连载长度"],
                    fill="toself",
                    name=label,
                    marker=dict(color=_CLUSTER_COLORS.get(label, "#333")),
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=False)),
                showlegend=True, height=350, margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    # ── Tab B：散点图 ─────────────────────────────────────────────────────────
    with tab_b:
        c1, c2 = st.columns(2)
        axis_mode = c1.selectbox("📈 探索空间坐标轴", [
            "主成分降维空间 (PCA1 vs PCA2)",
            "市场表现空间 (销量 vs 连载期)",
            "商业定位空间 (定价 vs 评分)",
        ])
        highlight_mode = c2.selectbox(
            "🎯 重点高亮品类",
            ["全选 (显示所有)"] + _LABEL_ORDER,
        )

        if "PCA" in axis_mode:
            x_col, y_col = "PCA1", "PCA2"
        elif "商业定位" in axis_mode:
            x_col, y_col = "Price_Num", "Rating_Num"
        else:
            x_col, y_col = "Issue_Num", "Sales_Num"

        title_col = (
            "Title" if "Title" in probe_df.columns
            else "Norm_Title" if "Norm_Title" in probe_df.columns
            else None
        )
        hover_cols = [c for c in ["Unit Sales", "Issue", "Price", "Rating", "Issue_Num"]
                      if c in probe_df.columns]
        existing_labels = [l for l in _LABEL_ORDER if l in probe_df["Cluster_Label"].unique()]

        # 高亮/虚化色系
        color_map = {
            label: (
                _CLUSTER_COLORS.get(label, "#333333")
                if highlight_mode == "全选 (显示所有)" or label == highlight_mode
                else "rgba(180,180,180,0.2)"
            )
            for label in existing_labels
        }

        # 散点尺寸
        size_series = pd.Series(10, index=probe_df.index)
        if highlight_mode != "全选 (显示所有)":
            mask = probe_df["Cluster_Label"] == highlight_mode
            size_series[mask] = 18
            size_series[~mask] = 4
        probe_df = probe_df.assign(Size=size_series)

        fig = px.scatter(
            probe_df, x=x_col, y=y_col,
            color="Cluster_Label", size="Size",
            hover_name=title_col, hover_data=hover_cols,
            color_discrete_map=color_map, height=550,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── 代表作检索 ────────────────────────────────────────────────────────────
    st.markdown("#### 🏆 簇群商业特征与代表作检索")
    cols = st.columns(4)
    render_funcs = [cols[0].info, cols[1].error, cols[2].success, cols[3].warning]
    icons = ["🔵", "🔴", "🟢", "🟠"]

    for i, label in enumerate(_LABEL_ORDER):
        desc = _CLUSTER_DESC.get(label, "")
        top  = _get_top_titles(probe_df, label)
        render_funcs[i](
            f"**{icons[i]} {label}**\n\n"
            f"**商业特征**：{desc}\n\n"
            f"**算法实时捕获代表作**：\n{top}"
        )