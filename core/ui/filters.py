import streamlit as st

def render_filters(df, has_enriched):
    """侧边栏全局过滤器与状态指示灯"""
    with st.sidebar:
        st.title("🎛️ 分析控制台")
        
        with st.expander("⚙️ 引擎设置与全局数据切片", expanded=True):
            api_key = st.text_input("SiliconFlow API Key", type="password")
            model_name = st.selectbox("分析模型", ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-7B-Instruct"])
            
            st.divider()
            publisher_filter = st.multiselect("出版商 (Publisher)", sorted(df["Studio/Pub"].dropna().unique()))
            
            min_yr, max_yr = int(df["Release Year"].min()), int(df["Release Year"].max())
            year_range = st.slider("发行年份 (Year)", min_yr, max_yr, (min_yr, max_yr))
            
            min_sls, max_sls = int(df["Unit Sales"].min()), int(df["Unit Sales"].max())
            sales_range = st.slider("销量区间 (Sales)", min_sls, max_sls, (min_sls, max_sls))

        # 动态过滤
        filtered_df = df.copy()
        if publisher_filter: 
            filtered_df = filtered_df[filtered_df["Studio/Pub"].isin(publisher_filter)]
        filtered_df = filtered_df[filtered_df["Release Year"].between(year_range[0], year_range[1])]
        filtered_df = filtered_df[filtered_df["Unit Sales"].between(sales_range[0], sales_range[1])]

        st.divider()
        st.markdown("### 🚦 系统引擎状态")
        st.markdown(f"**管线富化**: {'🟢 就绪' if has_enriched else '🟡 基础模式'}")
        st.markdown(f"**数据缓存**: {'🟢 命中'}")
        st.markdown(f"**LLM 连接**: {'🟢 等待唤醒' if api_key else '🔴 缺少密钥'}")

    return filtered_df, api_key, model_name