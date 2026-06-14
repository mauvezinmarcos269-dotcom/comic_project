import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.clustering import perform_advanced_clustering

def render_cluster_probe(probe_df):
    # 1. 深度拷贝防止 SettingWithCopyWarning
    probe_df = probe_df.copy()
    
    st.markdown("### 🧠 智能聚类分析中心")
    
    # 提取模型元数据
    sil_score = probe_df['Silhouette_Score'].iloc[0] if 'Silhouette_Score' in probe_df.columns else 0.0
    var_sum = probe_df['PCA_Explained_Variance'].iloc[0] * 100 if 'PCA_Explained_Variance' in probe_df.columns else 0.0

    col1, col2 = st.columns(2)
    col1.metric("模型轮廓系数 (Silhouette)", f"{sil_score:.3f}", help="越接近 1 说明簇分离度越好。")
    col2.metric("PCA 方差解释率", f"{var_sum:.1f}%", help="前两个主成分对原始数据信息的覆盖度。")
    st.divider()

    # 2. 聚类统计摘要表与雷达图
    tab_a, tab_b = st.tabs(["📊 统计与多维雷达图", "🔍 空间分布散点图"])

    with tab_a:
        st.markdown("#### 📊 聚类群组统计特性中心")
        # 增加连载期数 (Issue_Num)，让老师看到四类漫画在连载时长上的明显区别
        summary = probe_df.groupby("Cluster_Label").agg({
            "Sales_Num": "mean", 
            "Price_Num": "mean", 
            "Rating_Num": "mean",
            "Issue_Num": "mean"
        }).round(2)
        st.dataframe(summary, use_container_width=True)

        # 动态雷达图 (引入归一化处理，防止销量数值碾压其他特征)
        st.markdown("#### 🎯 核心特征聚类中心对比")
        # 手动实现 MinMaxScaler 逻辑
        summary_norm = (summary - summary.min()) / (summary.max() - summary.min() + 1e-9)
        
        fig_radar = go.Figure()
        for label in summary_norm.index:
            data = summary_norm.loc[label]
            fig_radar.add_trace(go.Scatterpolar(
                r=[data['Sales_Num'], data['Price_Num'], data['Rating_Num'], data['Issue_Num']], 
                theta=['销量特征', '定价策略', '内容评分', '连载长度'],
                fill='toself', name=label
            ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, height=450)
        st.plotly_chart(fig_radar, use_container_width=True)

    with tab_b:
        c1, c2 = st.columns(2)
        axis_mode = c1.selectbox("📈 探索空间坐标轴", ["主成分降维空间 (PCA1 vs PCA2)", "市场表现 (销量 vs 连载期)"])
        
        # 固定下拉框顺序
        order = ["Blockbuster IP (大IP主线)", "Event Comics (独立大事件)", "Premium Series (精品限定)", "Long Tail (长尾市场)"]
        highlight_mode = c2.selectbox("🎯 重点高亮品类", ["全选 (显示所有)"] + order)

        x_col, y_col = ("PCA1", "PCA2") if "PCA" in axis_mode else ("Issue_Num", "Sales_Num")
        
        # 安全获取动态列名
        title_col = "Title" if "Title" in probe_df.columns else "Norm_Title" if "Norm_Title" in probe_df.columns else None
        hover_cols = [col for col in ["Unit Sales", "Price", "Rating"] if col in probe_df.columns]
        
        # 散点图高亮逻辑
        probe_df['Size'] = 10
        if highlight_mode != "全选 (显示所有)":
            mask = probe_df['Cluster_Label'] == highlight_mode
            probe_df.loc[mask, 'Size'], probe_df.loc[~mask, 'Size'] = 18, 4
            color_map = {label: (px.colors.qualitative.Plotly[i] if label == highlight_mode else "rgba(180,180,180,0.3)") 
                         for i, label in enumerate(order)}
        else:
            color_map = {label: px.colors.qualitative.Plotly[i] for i, label in enumerate(order)}

        fig = px.scatter(probe_df, x=x_col, y=y_col, color='Cluster_Label', size='Size',
                         hover_name=title_col, hover_data=hover_cols,
                         color_discrete_map=color_map, height=500)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # 3. 动态代表作提取 (严格按指定顺序渲染卡片)
    st.markdown("#### 🏆 簇群代表作检索")
    def get_top_titles(label, n=3):
        sub = probe_df[probe_df['Cluster_Label'] == label]
        if sub.empty: return "暂无数据"
        t_col = "Title" if "Title" in sub.columns else "Norm_Title"
        return "、".join(sub.nlargest(n, 'Sales_Num')[t_col].dropna().unique().tolist()) if t_col else "未知"

    cols = st.columns(4)
    # 按商业逻辑固定的顺序渲染，防止错乱
    display_configs = [
        (0, "🔵", order[0], cols[0].info),
        (1, "🔴", order[1], cols[1].error),
        (2, "🟢", order[2], cols[2].success),
        (3, "🟠", order[3], cols[3].warning)
    ]
    
    for idx, icon, label, render_func in display_configs:
        render_func(f"**{icon} {label}**\n\n算法自动捕获代表作:\n\n{get_top_titles(label)}")