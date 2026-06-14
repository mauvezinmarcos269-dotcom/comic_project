import streamlit as st

from data_cleaner import load_and_clean_comic_data
from core.config import ENRICHED_DATA_FILE
from core.ui.styles import inject_global_styles
from core.ui.welcome import show_welcome_page
from core.ui.filters import render_filters
from core.ui.chat import render_chat
from core.ui.dashboard import render_dashboard
from core.ui.cluster_probe import render_cluster_probe
from core.features.clustering import perform_advanced_clustering

st.set_page_config(
    page_title="美漫销量智能分析平台",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 1. 欢迎页拦截 ──────────────────────────────────────────────────────────────
if "welcome_done" not in st.session_state:
    st.session_state.welcome_done = False
if not st.session_state.welcome_done:
    show_welcome_page()
    st.stop()

# ── 2. 全局样式 ────────────────────────────────────────────────────────────────
inject_global_styles()

# ── 3. 数据载入（聚类结果全局固化，永远重新计算，杜绝列漂移）─────────────────────
@st.cache_data(show_spinner=True)
def load_and_prepare_global_data():
    """
    读取基础数据，全量运行聚类，固化 ML 基准标签。
    直接调用，无需 required_cols 判断；KMeans 在千条规模下耗时 < 0.5s。
    """
    df = load_and_clean_comic_data()
    df = perform_advanced_clustering(df)
    return df

try:
    global_df = load_and_prepare_global_data()
    has_enriched = ENRICHED_DATA_FILE.exists()
except Exception as e:
    st.error(f"数据集载入或算法基准初始化异常: {e}")
    st.stop()

# ── 4. 侧边栏筛选（基于固化 ML 标签的全局数据切片）────────────────────────────
filtered_df, api_key, model_name = render_filters(global_df, has_enriched)

# ── 5. 三标签页路由（app.py 只做路由，不含任何具体 UI 逻辑）────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 数据分析看板",
    "🤖 AI 智能问答",
    "🧠 聚类多维探针 (KMeans)"
])

with tab1:
    render_dashboard(filtered_df, has_enriched)

with tab2:
    render_chat(filtered_df, api_key, model_name)

with tab3:
    render_cluster_probe(filtered_df)