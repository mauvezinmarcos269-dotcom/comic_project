import streamlit as st
import pandas as pd
import plotly.express as px  # 使用 plotly 绘制交互式图表
from data_cleaner import load_and_clean_comic_data

st.set_page_config(page_title="美漫大数据智能问数平台", page_icon="🦇", layout="wide")

st.title("🦇 美漫大数据智能问数与分析平台")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 数据控制中心")
    uploaded_file = st.file_uploader("上传您的美漫 CSV 数据集 (不少于1000行)", type=["csv"])
    st.markdown("---")
    st.caption("中国人民大学信息学院期末项目演示")

# 加载并清洗数据
# 课程要求支持自定义数据测试 [cite: 60]，这里优先读取上传的文件，没有则读取/生成本地测试文件
file_to_load = uploaded_file if uploaded_file is not None else "comic_sales_raw.csv"
df = load_and_clean_comic_data(file_to_load)

# 模块一：数据概览展示
st.header("📊 1. 漫画多维度数据预览")
col1, col2, col3, col4 = st.columns(4)
col1.metric("总漫画期数", f"{df.shape[0]} 部")
col2.metric("涵盖出版商/工作室", f"{df['Studio/Pub'].nunique()} 个")
col3.metric("平均漫画页数", f"{int(df['Page Count'].mean())} 页")
col4.metric("平均读者评分", f"{df['Rating'].mean():.2f} / 10")

# 展示清洗后的表格数据
st.dataframe(df, use_container_width=True)

# 模块二：高级数据可视化
st.header("📈 2. 核心指标探索（可视化分析）")

view_col1, view_col2 = st.columns(2)

with view_col1:
    st.subheader("🏢 不同出版商/工作室的平均评分对比")
    # 使用 Plotly 绘制高阶柱状图
    fig_bar = px.bar(
        df.groupby('Studio/Pub', as_index=False)['Rating'].mean(),
        x='Studio/Pub', y='Rating', 
        labels={'Rating': '平均评分', 'Studio/Pub': '出版商/工作室'},
        color='Rating', color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with view_col2:
    st.subheader("📄 漫画页数 (Page Count) 与评分 (Rating) 的分布关系")
    # 散点图，观察是否有“书越厚分越高”的倾向，并按是否获奖(Has_Award)染色
    fig_scatter = px.scatter(
        df, x='Page Count', y='Rating', 
        color='Has_Award' if 'Has_Award' in df.columns else None,
        hover_name='Title',
        labels={'Page Count': '漫画页数', 'Rating': '评分', 'Has_Award': '是否获奖 (1=是)'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# 模块三：智能问数后台雏形
st.header("💬 3. 智能问数对话 Agent")
st.info("前端框架已成功绑定您的17列美漫数据集！请在下方输入您想查询的动漫规律：")
if prompt := st.chat_input("例如：分析一下 Marvel 和 DC 谁的平均页数更多？"):
    st.chat_message("user").markdown(prompt)
    st.chat_message("assistant").markdown(f"🤖 **智能体响应**：我已接收到关于字段的提问【{prompt}】。接下来我将指导你配置大模型接口，实现真正的数据库自动查询。")