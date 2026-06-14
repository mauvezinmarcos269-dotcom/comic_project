import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.clustering import perform_advanced_clustering

def render_cluster_probe(probe_df):
    # 1. 深度拷贝防止 SettingWithCopyWarning
    probe_df = probe_df.copy()
    
    st.markdown("### 🧠 美漫销量 KMeans 聚类多维特征探针")
    
    # 提取模型元数据
    sil_score = probe_df['Silhouette_Score'].iloc[0] if 'Silhouette_Score' in probe_df.columns else 0.0
    var_sum = probe_df['PCA_Explained_Variance'].iloc[0] * 100 if 'PCA_Explained_Variance' in probe_df.columns else 0.0

    # 顶部指标栏
    col1, col2 = st.columns(2)
    col1.metric("模型轮廓系数 (Silhouette)", f"{sil_score:.3f}", help="越接近 1 说明簇分离度越好。")
    col2.metric("PCA 方差解释率", f"{var_sum:.1f}%", help="前两个主成分对原始数据信息的覆盖度。")
    
    st.divider()

    # 2. 聚类统计摘要表与雷达图
    tab_a, tab_b = st.tabs(["📊 统计与雷达图", "🔍 空间分布散点图"])

    with tab_a:
        st.markdown("#### 📊 聚类群组统计特性")
        summary = probe_df.groupby("Cluster_Label").agg({
            "Sales_Num": "mean", "Price_Num": "mean", "Rating_Num": "mean"
        }).round(2)
        st.table(summary)

        # 动态雷达图
        fig_radar = go.Figure()
        for label in summary.index:
            data = summary.loc[label]
            fig_radar.add_trace(go.Scatterpolar(
                r=[data['Sales_Num']/1000, data['Price_Num'], data['Rating_Num']], 
                theta=['销量(k)', '价格', '评分'],
                fill='toself', name=label
            ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    with tab_b:
        # 散点图交互控制
        c1, c2 = st.columns(2)
        axis_mode = c1.selectbox("📈 探索空间坐标轴", ["主成分降维空间 (PCA1 vs PCA2)", "市场表现 (销量 vs 连载期)"])
        highlight_mode = c2.selectbox("🎯 重点高亮品类", ["全选 (显示所有)"] + list(probe_df['Cluster_Label'].unique()))

        x_col, y_col = ("PCA1", "PCA2") if "PCA" in axis_mode else ("Issue_Num", "Sales_Num")
        
        # 散点图高亮逻辑
        probe_df['Size'] = 10
        if highlight_mode != "全选 (显示所有)":
            mask = probe_df['Cluster_Label'] == highlight_mode
            probe_df.loc[mask, 'Size'], probe_df.loc[~mask, 'Size'] = 18, 4
            color_map = {label: (color if label == highlight_mode else "rgba(180,180,180,0.3)") 
                         for label, color in zip(probe_df['Cluster_Label'].unique(), px.colors.qualitative.Plotly)}
        else:
            color_map = None

        fig = px.scatter(probe_df, x=x_col, y=y_col, color='Cluster_Label', size='Size',
                         hover_name="Title", hover_data=["Unit Sales", "Price", "Rating"],
                         color_discrete_map=color_map, height=500)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # 3. 动态代表作提取
    st.markdown("#### 🏆 簇群代表作检索")
    def get_top_titles(label, n=3):
        sub = probe_df[probe_df['Cluster_Label'] == label]
        return "、".join(sub.nlargest(n, 'Sales_Num')['Title'].dropna().unique().tolist()) if not sub.empty else "暂无数据"

    cols = st.columns(4)
    labels = probe_df['Cluster_Label'].unique()
    for i, label in enumerate(sorted(labels)):
        cols[i % 4].info(f"**{label}**\n\n代表作: {get_top_titles(label)}")