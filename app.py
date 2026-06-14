import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.clustering import perform_advanced_clustering

def render_cluster_probe(probe_df):
    probe_df = probe_df.copy() # 深度拷贝防报错
    st.markdown("### 🧠 智能聚类分析中心")
    
    sil_score = probe_df['Silhouette_Score'].iloc[0] if 'Silhouette_Score' in probe_df.columns else 0.0
    var_sum = probe_df['PCA_Explained_Variance'].iloc[0] * 100 if 'PCA_Explained_Variance' in probe_df.columns else 0.0

    col1, col2 = st.columns(2)
    col1.metric("模型轮廓系数 (Silhouette)", f"{sil_score:.3f}", help="越接近 1 说明簇分离度越好。")
    col2.metric("PCA 方差解释率", f"{var_sum:.1f}%", help="前两个主成分对原始数据信息的覆盖度。")
    st.divider()

    tab_a, tab_b = st.tabs(["📊 统计与分布画像", "🔍 空间降维散点图"])

    with tab_a:
        col_t1, col_t2 = st.columns([1, 1])
        
        with col_t1:
            st.markdown("#### 📊 聚类群组统计特性中心")
            summary = probe_df.groupby("Cluster_Label").agg({
                "Sales_Num": "mean", "Price_Num": "mean", "Rating_Num": "mean", "Issue_Num": "mean"
            }).round(2)
            st.dataframe(summary, use_container_width=True)

            st.markdown("#### 📈 聚类群组规模分布 (长尾验证)")
            cluster_counts = probe_df['Cluster_Label'].value_counts().reset_index()
            cluster_counts.columns = ['Cluster', 'Count']
            fig_bar = px.bar(cluster_counts, x='Cluster', y='Count', color='Cluster', text='Count',
                             color_discrete_sequence=px.colors.qualitative.Plotly)
            fig_bar.update_layout(showlegend=False, xaxis_title="聚类群体", yaxis_title="漫画数量", height=320, margin=dict(b=0, t=30))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_t2:
            st.markdown("#### 🎯 核心特征聚类中心热力图 (归一化)")
            # 严格 MinMaxScaler
            summary_norm = (summary - summary.min()) / (summary.max() - summary.min() + 1e-9)
            
            # 高表现力的聚类中心热力图
            fig_heat = px.imshow(
                summary_norm,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                labels=dict(x="特征维度", y="聚类群体", color="归一化强度")
            )
            # 优化坐标轴显示，更具 BI 风格
            fig_heat.update_xaxes(side="top")
            fig_heat.update_layout(height=300, margin=dict(t=50, b=10))
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("#### 🕸️ 聚类中心多维雷达图")
            fig_radar = go.Figure()
            for label in summary_norm.index:
                data = summary_norm.loc[label]
                fig_radar.add_trace(go.Scatterpolar(
                    r=[data['Sales_Num'], data['Price_Num'], data['Rating_Num'], data['Issue_Num']], 
                    theta=['销量特征', '定价策略', '内容评分', '连载长度'],
                    fill='toself', name=label
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_radar, use_container_width=True)

    with tab_b:
        c1, c2 = st.columns(2)
        axis_mode = c1.selectbox("📈 探索空间坐标轴", ["主成分降维空间 (PCA1 vs PCA2)", "市场表现 (销量 vs 连载期)"])
        
        order = ["Blockbuster IP (大IP主线)", "Event Comics (独立大事件)", "Premium Series (精品限定)", "Long Tail (长尾市场)"]
        highlight_mode = c2.selectbox("🎯 重点高亮品类", ["全选 (显示所有)"] + order)

        x_col, y_col = ("PCA1", "PCA2") if "PCA" in axis_mode else ("Issue_Num", "Sales_Num")
        
        title_col = "Title" if "Title" in probe_df.columns else "Norm_Title" if "Norm_Title" in probe_df.columns else None
        hover_cols = [col for col in ["Unit Sales", "Price", "Rating", "Issue_Num"] if col in probe_df.columns]
        
        existing_labels = [label for label in order if label in probe_df['Cluster_Label'].unique()]
        
        # 🌟 修复：使用更规范的 Series 索引映射控制散点大小
        size_series = pd.Series(10, index=probe_df.index)
        
        if highlight_mode != "全选 (显示所有)":
            mask = probe_df['Cluster_Label'] == highlight_mode
            size_series[mask] = 18
            size_series[~mask] = 4
            color_map = {label: (px.colors.qualitative.Plotly[i] if label == highlight_mode else "rgba(180,180,180,0.3)") 
                         for i, label in enumerate(existing_labels)}
        else:
            color_map = {label: px.colors.qualitative.Plotly[i] for i, label in enumerate(existing_labels)}

        probe_df['Size'] = size_series

        fig = px.scatter(probe_df, x=x_col, y=y_col, color='Cluster_Label', size='Size',
                         hover_name=title_col, hover_data=hover_cols,
                         color_discrete_map=color_map, height=550)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏆 簇群代表作检索")
    def get_top_titles(label, n=3):
        sub = probe_df[probe_df['Cluster_Label'] == label]
        if sub.empty: return "暂无数据"
        if "Title" in sub.columns:
            t_col = "Title"
        elif "Norm_Title" in sub.columns:
            t_col = "Norm_Title"
        else:
            return "未知"
        titles = sub.nlargest(n, 'Sales_Num')[t_col].dropna().unique().tolist()
        return "、".join(titles) if titles else "暂无"

    cols = st.columns(4)
    display_configs = [
        (0, "🔵", order[0], cols[0].info),
        (1, "🔴", order[1], cols[1].error),
        (2, "🟢", order[2], cols[2].success),
        (3, "🟠", order[3], cols[3].warning)
    ]
    
    for idx, icon, label, render_func in display_configs:
        render_func(f"**{icon} {label}**\n\n算法自动捕获代表作:\n\n{get_top_titles(label)}")