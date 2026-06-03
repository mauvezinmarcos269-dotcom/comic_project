import streamlit as st
from data_cleaner import load_and_clean_comic_data, ENRICHED_DATA_FILE
from core.agent.comic_agent import ask_agent
from core.visualization.charts import (
    plot_correlation_heatmap, plot_pca_clusters, plot_time_series_trend, 
    plot_word_freq, plot_decade_top10, plot_marvel_vs_dc_trend, 
    plot_publisher_share, plot_rating_vs_sales,
    plot_top_creators  
)
from core.features.advanced_analytics import perform_pca_clustering, perform_regression, extract_title_keywords

st.set_page_config(page_title="美漫大数据智能问数平台", page_icon="📊", layout="wide")
st.title("📊 美漫大数据智能问数与高级分析平台")
st.caption("基于高级数据管线与多维统计分析(PCA/聚类/NLP)打造的终期项目")

try:
    df = load_and_clean_comic_data()
    has_enriched = ENRICHED_DATA_FILE.exists()
except Exception as e:
    st.error(f"数据集加载失败: {e}")
    st.stop()

# --- 1. 宏观看板 ---
st.header("1. 行业宏观看板")
cols = st.columns(4)
cols[0].metric("总计样本量", f"{df.shape[0]} 条")
cols[1].metric("活跃出版商", f"{df['Studio/Pub'].nunique()} 家")
cols[2].metric("平均单册销量", f"{df['Unit Sales'].mean():,.0f} 册")
cols[3].metric("数据状态", "✨ 已富化" if has_enriched else "⚠️ 基础表")

# --- 2. 深度分析与可视化视图 ---
st.header("2. 深度数据挖掘与可视化")
tabs = st.tabs([
    "📈 市场大盘与对决", "🥧 出版商份额", "⭐️ 口碑与销量", 
    "🔥 相关性热力图", "🧬 聚类与回归", "📝 文本与榜单"
])

with tabs[0]:
    st.plotly_chart(plot_time_series_trend(df), use_container_width=True)
    st.plotly_chart(plot_marvel_vs_dc_trend(df), use_container_width=True)

with tabs[1]:
    st.plotly_chart(plot_publisher_share(df), use_container_width=True)

with tabs[2]:
    # 融合：智能降级与主创大屏透视
    rating_fig = plot_rating_vs_sales(df)
    
    if rating_fig is not None:
        # 如果评分数据充足（正常情况），则渲染散点图
        st.plotly_chart(rating_fig, use_container_width=True)
    else:
        # 【智能降级与跨界富化】：若无有效评分，则展示更具技术含量的 Top 20 核心主创大屏
        st.info("💡 提示：当前数据集未检测到充足的 Rating(评分) 维度，系统已自动触发“金牌创作者多维销售图谱”进行数据补足替代。")
        
        creator_col1, creator_col2 = st.columns(2)
        
        with creator_col1:
            writer_fig = plot_top_creators(df, role="Writer", top_n=20)
            if writer_fig:
                st.plotly_chart(writer_fig, use_container_width=True)
            else:
                st.warning("暂无有效编剧销量数据，请先执行 pipeline 富化管线。")
                
        with creator_col2:
            artist_fig = plot_top_creators(df, role="Artist", top_n=20)
            if artist_fig:
                st.plotly_chart(artist_fig, use_container_width=True)
            else:
                st.warning("暂无有效画师销量数据，请先执行 pipeline 富化管线。")

with tabs[3]:
    method = st.radio("相关系数计算法", ["spearman", "pearson"], horizontal=True)
    heatmap = plot_correlation_heatmap(df, method)
    if heatmap: st.plotly_chart(heatmap, use_container_width=True)
    else: st.warning("有效数值特征不足，热力图无法生成。")

with tabs[4]:
    col1, col2 = st.columns(2)
    with col1:
        pca_df = perform_pca_clustering(df, 4)
        if pca_df is not None: st.plotly_chart(plot_pca_clusters(pca_df), use_container_width=True)
        else: st.info("数据量不足以聚类。")
    with col2:
        st.markdown("#### 价格销量 OLS 线性回归")
        _, summary = perform_regression(df)
        if summary: st.text(summary)
        else: st.info("回归失败。")

with tabs[5]:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_word_freq(extract_title_keywords(df)), use_container_width=True)
    with col2:
        st.plotly_chart(plot_decade_top10(df), use_container_width=True)

# --- 3. 智能问答 ---
st.header("3. 💬 智能自然语言终端")
prompt = st.text_input("请输入指令：", placeholder="例如：漫威和DC谁厉害？")
if prompt:
    with st.spinner("AI 引擎解析中..."):
        ans, chart = ask_agent(prompt, df)
        st.markdown("---")
        st.markdown(ans)
        if chart: st.plotly_chart(chart, use_container_width=True)