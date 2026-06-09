import streamlit as st
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

# 4. 侧边栏与主看板渲染
filtered_df, api_key, model_name = render_filters(df, has_enriched)

tab_dash, tab_chat = st.tabs(["📊 数据分析看板", "🤖 AI 智能问答"])

with tab_dash:
    render_dashboard(filtered_df, has_enriched)

with tab_chat:
    render_chat(filtered_df, api_key, model_name)