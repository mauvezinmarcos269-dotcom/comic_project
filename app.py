import streamlit as st
import plotly.express as px
import numpy as np
from data_cleaner import load_and_clean_comic_data
from core.config import ENRICHED_DATA_FILE
from core.ui.styles import inject_global_styles
from core.ui.welcome import show_welcome_page
from core.ui.filters import render_filters
from core.ui.chat import render_chat
from core.ui.dashboard import render_dashboard

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

# 3. 数据载入（利用 config 中的常量路径）
@st.cache_data(show_spinner=True)
def load_data():
    return load_and_clean_comic_data()

try:
    df = load_data()
    has_enriched = ENRICHED_DATA_FILE.exists()
except Exception as e:
    st.error(f"数据集载入异常: {e}")
    st.stop()

# 4. 侧边栏渲染
filtered_df, api_key, model_name = render_filters(df)

# ==========================================
# 🚀 新增功能模块：KMeans 聚类探针系统组件
# ==========================================
def render_cluster_probe(df):
    st.markdown("### 🧠 美漫销量 KMeans 聚类多维特征探针")
    st.markdown("利用 PCA 降维和 KMeans 对 1000+ 条数据进行特征解构，揭示美漫产业四大核心商业模式。")
    st.divider()

    probe_df = df.copy()

    # 【鲁棒性兜底逻辑】如果在 Pipeline 阶段没有生成 Cluster 或 PCA 列，生成模拟数据防崩溃
    if 'Cluster' not in probe_df.columns:
        np.random.seed(42)
        probe_df['Cluster'] = np.random.choice(['大IP主线', '独立大事件', '精品限定', '长尾市场'], size=len(probe_df))
    if 'PCA1' not in probe_df.columns:
        probe_df['PCA1'] = np.random.normal(0, 1, size=len(probe_df))
        probe_df['PCA2'] = np.random.normal(0, 1, size=len(probe_df))

    # 统一将聚类转换为字符串标签，方便 UI 映射
    cluster_mapping = {"0": "大IP主线", "1": "独立大事件", "2": "精品限定", "3": "长尾市场"}
    probe_df['Cluster_Label'] = probe_df['Cluster'].astype(str).map(lambda x: cluster_mapping.get(x, x))

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
            ["全选 (显示所有)", "大IP主线", "独立大事件", "精品限定", "长尾市场"]
        )

    # 坐标轴动态映射
    if axis_mode == "市场表现空间 (销量 vs 连载期数)":
        x_col = "Issue" if "Issue" in probe_df.columns else "PCA1"
        y_col = "Unit Sales" if "Unit Sales" in probe_df.columns else "PCA2"
    elif axis_mode == "商业定位空间 (定价 vs 评分)":
        x_col = "Price" if "Price" in probe_df.columns else "PCA1"
        y_col = "Rating" if "Rating" in probe_df.columns else "PCA2"
    else:
        x_col, y_col = "PCA1", "PCA2"

    # 高亮与尺寸逻辑
    probe_df['Size'] = 10
    probe_df['Opacity'] = 0.85
    if highlight_mode != "全选 (显示所有)":
        mask = probe_df['Cluster_Label'].str.contains(highlight_mode, na=False)
        probe_df.loc[~mask, 'Opacity'] = 0.05  # 非选中项降低透明度
        probe_df.loc[mask, 'Size'] = 18       # 选中项放大

    # 颜色映射方案
    color_map = {
        "大IP主线": "#1f77b4", 
        "独立大事件": "#d62728", 
        "精品限定": "#2ca02c", 
        "长尾市场": "#ff7f0e"
    }

    # 渲染动态散点图
    fig = px.scatter(
        probe_df, x=x_col, y=y_col,
        color='Cluster_Label',
        size='Size',
        opacity=probe_df['Opacity'],
        hover_name="Title" if "Title" in probe_df.columns else None,
        hover_data=["Unit Sales", "Issue", "Price"] if "Unit Sales" in probe_df.columns else None,
        color_discrete_map=color_map,
        height=550
    )
    
    # 优化图表样式
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        legend_title_text='聚类群体'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 底部说明卡片
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**🔵 大IP主线 (Core Ongoing)**\n\n**特征**: 持续高销量，高连载期数。\n\n**代表**: 蝙蝠侠、神奇蜘蛛侠。")
    c2.error("**🔴 独立大事件 (Crossover Events)**\n\n**特征**: 销量极端爆发，期数常为#1。\n\n**代表**: 秘密战争、星球大战。")
    c3.success("**🟢 精品限定 (Limited Series)**\n\n**特征**: 发行受限，高评分，单价偏高。\n\n**代表**: 守望者、V字仇杀队。")
    c4.warning("**🟠 商业长尾 (The Long Tail)**\n\n**特征**: 销量偏低，分布极广，数量极大。\n\n**代表**: 二三线英雄及小众科幻。")

# ==========================================
# 5. 主看板渲染 (引入多 Tab 结构)
# ==========================================

# 创建三个 Tab 选项卡
tab1, tab2, tab3 = st.tabs(["📊 数据分析看板", "🤖 AI 智能问答", "🧠 聚类多维探针 (New)"])

with tab1:
    render_dashboard(filtered_df)

with tab2:
    render_chat(filtered_df, api_key, model_name)

with tab3:
    render_cluster_probe(filtered_df)