import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.features.clustering import perform_advanced_clustering
from sklearn.preprocessing import MinMaxScaler

def render_cluster_probe(probe_df):
    probe_df = probe_df.copy()
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
            
            # 使用固定色系保证色彩不漂移
            base_colors = {
                "Blockbuster IP (大IP主线)": "#1f77b4",
                "Event Comics (独立大事件)": "#d62728",
                "Premium Series (精品限定)": "#2ca02c",
                "Long Tail (长尾市场)": "#ff7f0e"
            }
            
            fig_bar = px.bar(cluster_counts, x='Cluster', y='Count', color='Cluster', text='Count',
                             color_discrete_map=base_colors)
            fig_bar.update_layout(showlegend=False, xaxis_title="聚类群体", yaxis_title="漫画数量", height=320, margin=dict(b=0, t=30))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_t2:
            st.markdown("#### 🎯 核心特征聚类中心热力图")
            # 严格使用 MinMaxScaler 规范化
            summary_norm = pd.DataFrame(
                MinMaxScaler().fit_transform(summary),
                columns=summary.columns,
                index=summary.index
            )
            
            fig_heat = px.imshow(
                summary_norm, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r",
                labels=dict(x="特征维度", y="聚类群体", color="归一化强度")
            )
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
                    fill='toself', name=label, marker=dict(color=base_colors.get(label, "#333"))
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_radar, use_container_width=True)

    with tab_b:
        c1, c2 = st.columns(2)
        # 恢复所有坐标轴探索选项
        axis_mode = c1.selectbox("📈 探索空间坐标轴", [
            "主成分降维空间 (PCA1 vs PCA2)", 
            "市场表现 (销量 vs 连载期)", 
            "商业定位 (定价 vs 评分)"
        ])
        
        order = ["Blockbuster IP (大IP主线)", "Event Comics (独立大事件)", "Premium Series (精品限定)", "Long Tail (长尾市场)"]
        highlight_mode = c2.selectbox("🎯 重点高亮品类", ["全选 (显示所有)"] + order)

        # 动态解析坐标轴
        if "PCA" in axis_mode:
            x_col, y_col = "PCA1", "PCA2"
        elif "商业定位" in axis_mode:
            x_col, y_col = "Price_Num", "Rating_Num"
        else:
            x_col, y_col = "Issue_Num", "Sales_Num"
        
        title_col = "Title" if "Title" in probe_df.columns else "Norm_Title" if "Norm_Title" in probe_df.columns else None
        hover_cols = [col for col in ["Unit Sales", "Price", "Rating", "Issue_Num"] if col in probe_df.columns]
        existing_labels = [label for label in order if label in probe_df['Cluster_Label'].unique()]
        
        # 规范化构建颜色映射
        color_map = {}
        for label in existing_labels:
            if highlight_mode != "全选 (显示所有)" and label != highlight_mode:
                color_map[label] = "rgba(180,180,180,0.3)"
            else:
                color_map[label] = base_colors.get(label, "#333333")

        size_series = pd.Series(10, index=probe_df.index)
        if highlight_mode != "全选 (显示所有)":
            mask = probe_df['Cluster_Label'] == highlight_mode
            size_series[mask] = 18
            size_series[~mask] = 4

        probe_df['Size'] = size_series

        fig = px.scatter(probe_df, x=x_col, y=y_col, color='Cluster_Label', size='Size',
                         hover_name=title_col, hover_data=hover_cols,
                         color_discrete_map=color_map, height=550)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏆 簇群商业特征与代表作检索")
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
    desc_map = {
        order[0]: "持续高销量，高连载长度",
        order[1]: "销量极端爆发，期数常为#1或#0",
        order[2]: "发行受限，高评分，单价偏高",
        order[3]: "销量偏低，分布极广，数量极大"
    }
    
    display_configs = [
        (0, "🔵", order[0], cols[0].info),
        (1, "🔴", order[1], cols[1].error),
        (2, "🟢", order[2], cols[2].success),
        (3, "🟠", order[3], cols[3].warning)
    ]
    
    for idx, icon, label, render_func in display_configs:
        desc = desc_map.get(label, "")
        render_func(f"**{icon} {label}**\n\n**特征**：{desc}\n\n**代表作**：\n{get_top_titles(label)}")