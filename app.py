import streamlit as st
import pandas as pd
import plotly.express as px

from data_cleaner import load_and_clean_comic_data
from core.config import ENRICHED_DATA_FILE
from core.ui.styles import inject_global_styles
from core.ui.welcome import show_welcome_page
from core.ui.filters import render_filters
from core.ui.chat import render_chat
from core.ui.dashboard import render_dashboard
from core.features.clustering import perform_advanced_clustering

# 页面基础配置
st.set_page_config(page_title="美漫销量智能分析平台", page_icon="🦸", layout="wide", initial_sidebar_state="expanded")

# 1. 状态初始化与拦截
if "welcome_done" not in st.session_state:
    st.session_state.welcome_done = False
if not st.session_state.welcome_done:
    show_welcome_page()
    st.stop()

# 2. UI 环境加载
inject_global_styles()

# 3. 数据载入与全局聚类守护
@st.cache_data(show_spinner=True)
def load_and_prepare_global_data():
    """读取数据，并确保全局仅聚类一次，避免筛选后簇漂移"""
    df = load_and_clean_comic_data()
    # 如果 Pipeline 没有运行聚类，就在这里补救执行一次并缓存
    if 'Cluster_Label' not in df.columns or 'PCA1' not in df.columns:
        df = perform_advanced_clustering(df)
    return df

try:
    global_df = load_and_prepare_global_data()
    has_enriched = ENRICHED_DATA_FILE.exists()
except Exception as e:
    st.error(f"数据集载入异常: {e}")
    st.stop()

# 4. 侧边栏渲染 (只对全量聚类后的数据进行过滤)
filtered_df, api_key, model_name = render_filters(global_df, has_enriched)

# ==========================================
# 5. 聚类探针系统组件 (安全、动态、专业)
# ==========================================
def render_cluster_probe(probe_df):
    st.markdown("### 🧠 美漫销量 KMeans 聚类多维特征探针")
    
    # 提取全局的轮廓系数
    sil_score = probe_df['Silhouette_Score'].iloc[0] if 'Silhouette_Score' in probe_df.columns else 0.0
    
    col_text, col_metric = st.columns([8, 2])
    with col_text:
        st.markdown("基于 `scikit-learn` 对 **7维业务特征** 进行 PCA 降维与 KMeans 无监督聚类，揭示美漫产业四大核心商业模式。")
    with col_metric:
        st.metric(label="模型轮廓系数 (Silhouette)", value=f"{sil_score:.3f}", 
                  help="衡量聚类质量的指标，越接近 1 说明簇分离度越好。")
    st.divider()

    # 控制台布局
    col1, col2 = st.columns(2)
    with col1:
        axis_mode = st.selectbox(
            "📈 探索空间坐标轴",
            ["主成分降维空间 (PCA1 vs PCA2)", "市场表现空间 (销量 vs 连载期数)", "商业定位空间 (定价 vs 评分)"]
        )
    with col2:
        highlight_mode = st.selectbox(
            "🎯 重点高亮品类",
            ["全选 (显示所有)", "Blockbuster IP (大IP主线)", "Event Comics (独立大事件)", "Premium Series (精品限定)", "Long Tail (长尾市场)"]
        )

    # 坐标轴安全映射
    if axis_mode == "市场表现空间 (销量 vs 连载期数)":
        x_col, y_col = "Issue_Num", "Sales_Num"
    elif axis_mode == "商业定位空间 (定价 vs 评分)":
        x_col, y_col = "Price_Num", "Rating_Num"
    else:
        x_col, y_col = "PCA1", "PCA2"

    # 安全构建 Hover 数据列
    hover_cols = []
    for c in ["Unit Sales", "Issue", "Price", "Rating"]:
        if c in probe_df.columns:
            hover_cols.append(c)

    # 使用分组逻辑与 Size 控制高亮，彻底抛弃可能报错的 opacity
    probe_df['Size'] = 10
    base_colors = {
        "Blockbuster IP (大IP主线)": "#1f77b4", 
        "Event Comics (独立大事件)": "#d62728", 
        "Premium Series (精品限定)": "#2ca02c", 
        "Long Tail (长尾市场)": "#ff7f0e"
    }
    
    active_color_map = base_colors.copy()
    if highlight_mode != "全选 (显示所有)":
        mask = probe_df['Cluster_Label'] == highlight_mode
        probe_df.loc[mask, 'Size'] = 18
        probe_df.loc[~mask, 'Size'] = 4
        for key in active_color_map.keys():
            if key != highlight_mode:
                active_color_map[key] = "rgba(180, 180, 180, 0.3)" # 非选中项变灰

    # 渲染动态散点图
    fig = px.scatter(
        probe_df, x=x_col, y=y_col,
        color='Cluster_Label',
        size='Size',
        hover_name="Title" if "Title" in probe_df.columns else None,
        hover_data=hover_cols,
        color_discrete_map=active_color_map,
        height=550
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        legend_title_text='聚类群体 (ML Labels)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 动态提取各簇的 Top 3 代表作 (杜绝写死)
    def get_top_titles(df, label, n=3):
        sub = df[df['Cluster_Label'] == label]
        if sub.empty: return "暂无数据"
        titles = sub.nlargest(n, 'Sales_Num')['Title'].dropna().unique().tolist()
        return "、".join(titles) if titles else "未知"

    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**🔵 Blockbuster IP (大IP主线)**\n\n**特征**: 持续高销量，高连载期数。\n\n**算法代表**: {get_top_titles(probe_df, 'Blockbuster IP (大IP主线)')}")
    c2.error(f"**🔴 Event Comics (独立大事件)**\n\n**特征**: 销量极端爆发，期数常为#1。\n\n**算法代表**: {get_top_titles(probe_df, 'Event Comics (独立大事件)')}")
    c3.success(f"**🟢 Premium Series (精品限定)**\n\n**特征**: 发行受限，高评分，单价偏高。\n\n**算法代表**: {get_top_titles(probe_df, 'Premium Series (精品限定)')}")
    c4.warning(f"**🟠 Long Tail (长尾市场)**\n\n**特征**: 销量偏低，分布极广，数量极大。\n\n**算法代表**: {get_top_titles(probe_df, 'Long Tail (长尾市场)')}")

# ==========================================
# 6. 整合多 Tab 结构
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 数据分析看板", "🤖 AI 智能问答", "🧠 聚类多维探针 (KMeans)"])

with tab1:
    render_dashboard(filtered_df, has_enriched)

with tab2:
    render_chat(filtered_df, api_key, model_name)

with tab3:
    render_cluster_probe(filtered_df)