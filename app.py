import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

from data_cleaner import load_and_clean_comic_data
from core.config import ENRICHED_DATA_FILE
from core.ui.styles import inject_global_styles
from core.ui.welcome import show_welcome_page
from core.ui.filters import render_filters
from core.ui.chat import render_chat
from core.ui.dashboard import render_dashboard
from core.features.clustering import perform_advanced_clustering

# 页面基础配置
st.set_page_config(page_title="美漫销量智能分析平台", page_icon="🦇", layout="wide", initial_sidebar_state="expanded")

# 1. 欢迎页拦截与状态守护
if "welcome_done" not in st.session_state:
    st.session_state.welcome_done = False
if not st.session_state.welcome_done:
    show_welcome_page()
    st.stop()

# 2. UI 全局样式加载
inject_global_styles()

# 3. 数据载入：确保全局全量数据仅聚类一次，拒绝交互筛选后的标签漂移
@st.cache_data(show_spinner=True)
def load_and_prepare_global_data():
    """读取基础数据，全量运行预计算聚类，固化 ML 基准标签"""
    df = load_and_clean_comic_data()
    
    # 防御性检查：确保所有模型所需要的 ML 衍生列均已固化在全局数据中
    required_cols = ['Cluster_Label', 'Cluster', 'PCA1', 'PCA2', 'Silhouette_Score', 'PCA_Explained_Variance']
    if not all(col in df.columns for col in required_cols):
        df = perform_advanced_clustering(df)
    return df

try:
    global_df = load_and_prepare_global_data()
    has_enriched = ENRICHED_DATA_FILE.exists()
except Exception as e:
    st.error(f"数据集载入或算法基准初始化异常: {e}")
    st.stop()

# 4. 侧边栏多维筛选（基于带有固化 ML 标签的全局数据进行切片视图过滤）
filtered_df, api_key, model_name = render_filters(global_df, has_enriched)

# =========================================================================
# 🧠 5. 聚类多维探针分析中心组件 (内嵌整合，解决所有潜在 Bug，确保 100% 运行)
# =========================================================================
def render_cluster_probe(probe_df):
    probe_df = probe_df.copy()  # 显式深度拷贝，完全规避 SettingWithCopyWarning
    st.markdown("### 🧠 智能聚类分析中心")
    
    # 动态抓取全局机器学习模型的元数据
    sil_score = probe_df['Silhouette_Score'].iloc[0] if 'Silhouette_Score' in probe_df.columns else 0.0
    var_sum = probe_df['PCA_Explained_Variance'].iloc[0] * 100 if 'PCA_Explained_Variance' in probe_df.columns else 0.0

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("模型轮廓系数 (Silhouette)", f"{sil_score:.3f}", help="越接近 1 说明簇分离度与内聚度越好。")
    col_m2.metric("PCA 特征方差解释率", f"{var_sum:.1f}%", help="前两个主成分对原始 7 维特征空间信息的覆盖度。")
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

            st.markdown("#### 📈 聚类群组规模分布 (长尾效应量化验证)")
            cluster_counts = probe_df['Cluster_Label'].value_counts().reset_index()
            cluster_counts.columns = ['Cluster', 'Count']
            
            # 全局绑定固定色系，规避数据缺失带来的色带次序漂移
            base_colors = {
                "Blockbuster IP (大IP主线)": "#1f77b4",
                "Event Comics (独立大事件)": "#d62728",
                "Premium Series (精品限定)": "#2ca02c",
                "Long Tail (长尾市场)": "#ff7f0e"
            }
            
            fig_bar = px.bar(cluster_counts, x='Cluster', y='Count', color='Cluster', text='Count',
                             color_discrete_map=base_colors)
            fig_bar.update_layout(showlegend=False, xaxis_title="聚类群体", yaxis_title="作品样本期数", height=320, margin=dict(b=0, t=30))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_t2:
            st.markdown("#### 🎯 核心特征聚类中心热力图")
            # 引入规范的 MinMaxScaler 进行归一化特征缩放，解决数据量纲不一产生的作图压制
            summary_norm = pd.DataFrame(
                MinMaxScaler().fit_transform(summary),
                columns=summary.columns,
                index=summary.index
            )
            
            # 彻底解决 IDE 类型检查器对 text_auto 的 Literal['.2f'] / bool 的冲突警告
            fig_heat = px.imshow(
                summary_norm, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r",
                labels=dict(x="特征维度", y="聚类群体", color="归一化强度")
            )
            fig_heat.update_traces(texttemplate="%{z:.2f}")  # 底层强制约束文本格式
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
        axis_mode = c1.selectbox("📈 探索空间坐标轴", [
            "主成分降维空间 (PCA1 vs PCA2)", 
            "市场表现空间 (销量 vs 连载期)", 
            "商业定位空间 (定价 vs 评分)"
        ])
        
        order = ["Blockbuster IP (大IP主线)", "Event Comics (独立大事件)", "Premium Series (精品限定)", "Long Tail (长尾市场)"]
        highlight_mode = c2.selectbox("🎯 重点高亮品类", ["全选 (显示所有)"] + order)

        # 动态安全的空间坐标系解析
        if "PCA" in axis_mode:
            x_col, y_col = "PCA1", "PCA2"
        elif "商业定位" in axis_mode:
            x_col, y_col = "Price_Num", "Rating_Num"
        else:
            x_col, y_col = "Issue_Num", "Sales_Num"
        
        # 极度安全的标题字段防空短路识别
        title_col = "Title" if "Title" in probe_df.columns else "Norm_Title" if "Norm_Title" in probe_df.columns else None
        
        # 恢复 Issue 文本列，确保在气泡中能够完整看到 Special、Annual、One-Shot 等商业信息描述
        target_hover_fields = ["Unit Sales", "Issue", "Price", "Rating", "Issue_Num"]
        hover_cols = [col for col in target_hover_fields if col in probe_df.columns]
        
        existing_labels = [label for label in order if label in probe_df['Cluster_Label'].unique()]
        
        # 散点图高亮与虚化配色字典构建
        color_map = {}
        for label in existing_labels:
            if highlight_mode != "全选 (显示所有)" and label != highlight_mode:
                color_map[label] = "rgba(180,180,180,0.2)"
            else:
                color_map[label] = base_colors.get(label, "#333333")

        # 摒弃脏操作，遵循规范使用基于 Index 的 Series 映射控制散点尺寸
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
        if "Title" in sub.columns: t_col = "Title"
        elif "Norm_Title" in sub.columns: t_col = "Norm_Title"
        else: return "数据源缺失标题字段"
        
        titles = sub.nlargest(n, 'Sales_Num')[t_col].dropna().unique().tolist()
        return "、".join(titles) if titles else "暂无代表作"

    cols = st.columns(4)
    desc_map = {
        order[0]: "持续高销量，极长的日常连载周数与历史积累",
        order[1]: "单期销量极端爆发突破常规，普遍集中在 #1 创刊号或年度联动节点",
        order[2]: "发行长度受限，内容评分中位数极高，具备更强的精品艺术属性与客单价",
        order[3]: "单刊日常销量处于中下游，但作品基数极其庞大，构成产业的基本长尾盘"
    }
    
    display_configs = [
        (0, "🔵", order[0], cols[0].info),
        (1, "🔴", order[1], cols[1].error),
        (2, "🟢", order[2], cols[2].success),
        (3, "🟠", order[3], cols[3].warning)
    ]
    
    for idx, icon, label, render_func in display_configs:
        desc = desc_map.get(label, "")
        render_func(f"**{icon} {label}**\n\n**商业特征**：{desc}\n\n**算法实时捕获代表作**：\n{get_top_titles(label)}")

# =========================================================================
# 6. 整合多 Tab 三级视窗闭环
# =========================================================================
tab1, tab2, tab3 = st.tabs(["📊 数据分析看板", "🤖 AI 智能问答", "🧠 聚类多维探针 (KMeans)"])

with tab1:
    render_dashboard(filtered_df, has_enriched)

with tab2:
    render_chat(filtered_df, api_key, model_name)

with tab3:
    render_cluster_probe(filtered_df)