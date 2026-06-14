import streamlit as st
import pandas as pd
from core.visualization.charts import (
    plot_correlation_heatmap,
    plot_time_series_trend,
    plot_word_freq,
    plot_marvel_vs_dc_trend,
    plot_publisher_share,
    plot_top_creators,
    plot_decade_top10,
)
from core.features.advanced_analytics import (
    extract_title_keywords,
    perform_regression,
)
from core.ui.export_utils import generate_dashboard_pdf, REPORTLAB_AVAILABLE

# ── 有价值的缓存：NLP 词频统计耗时较高 ────────────────────────────────────────
@st.cache_data
def get_keywords_cached(df: pd.DataFrame) -> pd.DataFrame:
    return extract_title_keywords(df)


# ── 无效占位符常量 ─────────────────────────────────────────────────────────────
_INVALID_VALUES = {"not available", "not enriched", "unknown", "none", "nan", "n/a", ""}


def get_top_entity(d: pd.DataFrame, col: str) -> tuple[str, int]:
    """返回指定列销量最高的有效实体名及其总销量，自动跳过占位符。"""
    if col not in d.columns or d.empty:
        return "N/A", 0
    valid_mask = ~d[col].astype(str).str.strip().str.lower().isin(_INVALID_VALUES)
    valid_d = d[valid_mask].copy()
    if valid_d.empty or "Unit Sales" not in valid_d.columns:
        return "N/A", 0
    s = valid_d.groupby(col)["Unit Sales"].sum().sort_values(ascending=False)
    if s.empty:
        return "N/A", 0
    return s.index[0], int(s.iloc[0])


def _best_char(d: pd.DataFrame) -> tuple[str, int]:
    """优先使用 Main_Character，若无有效值则回退到 Character 列。"""
    for col in ("Main_Character", "Character"):
        name, sales = get_top_entity(d, col)
        if name != "N/A":
            return name, sales
    return "N/A", 0


def render_dashboard(filtered_df: pd.DataFrame, has_enriched: bool) -> None:
    pub_name, _    = get_top_entity(filtered_df, "Studio/Pub")
    char_name, _   = _best_char(filtered_df)
    writer_name, _ = get_top_entity(filtered_df, "Writer")

    avg_sales   = filtered_df["Unit Sales"].mean() if len(filtered_df) else 0
    total_sales = filtered_df["Unit Sales"].sum() if len(filtered_df) else 0

    # ── KPI 卡 ────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("总计销售量",     f"{total_sales:,.0f}")
    k2.metric("单期平均销量",   f"{avg_sales:,.0f}")
    k3.metric("最畅销出版商",   pub_name)
    k4.metric("独立发行商数量", filtered_df["Studio/Pub"].nunique())

    # ── 元数据摘要 ────────────────────────────────────────────────────────────
    col_meta, col_summary = st.columns([1, 2])
    with col_meta:
        with st.expander("📑 Dataset Metadata", expanded=True):
            st.markdown(f"""
            - **Rows**: {len(filtered_df):,}
            - **Columns**: {len(filtered_df.columns)}
            - **Year Range**: {filtered_df['Release Year'].min()} – {filtered_df['Release Year'].max()}
            - **Missing Rate**: {round(filtered_df.isna().mean().mean() * 100, 2)}%
            """)
    with col_summary:
        summary_dict = {
            "Top Publisher": pub_name,
            "Top Character": char_name,
            "Top Writer":    writer_name,
            "Total Sales":   f"{total_sales:,.0f} units",
            "Avg Sales/Issue": f"{avg_sales:,.0f} units",
        }
        st.info(" | ".join([f"**{k}**: {v}" for k, v in summary_dict.items()]))

    # ── 导出按钮 ──────────────────────────────────────────────────────────────
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "📥 导出当前筛选 CSV",
            filtered_df.to_csv(index=False).encode("utf-8-sig"),
            "comic_data.csv",
            use_container_width=True,
        )
    with dl2:
        if REPORTLAB_AVAILABLE:
            pdf_bytes = generate_dashboard_pdf(summary_dict)
            st.download_button(
                "📄 导出 Executive Summary (PDF)",
                pdf_bytes, "executive_summary.pdf",
                use_container_width=True,
            )
        else:
            st.download_button(
                "📄 导出 PDF 报告 (尚未安装依赖)",
                b"", disabled=True,
                use_container_width=True,
            )
            st.caption("💡 终端执行 `pip install reportlab` 即可解锁 PDF 导出功能")

    st.divider()

    # ── 分析标签页
    tabs = st.tabs([
        "🔥 特征热力图",
        "📈 时间序列趋势",
        "🧮 销售回归",
        "📝 标题/角色 NLP",
        "🏆 十年年度销冠",
        "✍️ 顶尖创作者",
        "🦸 巨头市场份额",
    ])

    with tabs[0]:
        method = st.radio("选择相关系数计算法:", ["spearman", "pearson"], horizontal=True)
        fig_heat = plot_correlation_heatmap(filtered_df, method)
        if fig_heat:
            st.plotly_chart(fig_heat, use_container_width=True)

    with tabs[1]:
        fig_time = plot_time_series_trend(filtered_df)
        if fig_time:
            st.plotly_chart(fig_time, use_container_width=True)

    with tabs[2]:
        # 回归耗时极小，直接调用，无需 @st.cache_data 包装
        try:
            _, summary_str = perform_regression(filtered_df)
            if summary_str:
                st.text(summary_str)
            else:
                st.info("价格或销量样本不足，跳过回归分析。")
        except Exception as e:
            st.info(f"回归不可用: {e}")

    with tabs[3]:
        fig_word = plot_word_freq(get_keywords_cached(filtered_df))
        if fig_word:
            st.plotly_chart(fig_word, use_container_width=True)

    with tabs[4]:
        try:
            fig_dec = plot_decade_top10(filtered_df)
            if fig_dec:
                st.plotly_chart(fig_dec, use_container_width=True)
        except Exception:
            st.info("需要包含 2010–2019 年数据。")

    with tabs[5]:
        c1, c2 = st.columns(2)
        with c1:
            if "Writer" in filtered_df.columns:
                f_w = plot_top_creators(filtered_df, "Writer", 20)
                if f_w:
                    st.plotly_chart(f_w, use_container_width=True)
        with c2:
            if "Artist" in filtered_df.columns:
                f_a = plot_top_creators(filtered_df, "Artist", 20)
                if f_a:
                    st.plotly_chart(f_a, use_container_width=True)

    with tabs[6]:
        c1, c2 = st.columns(2)
        with c1:
            f_md = plot_marvel_vs_dc_trend(filtered_df)
            if f_md:
                st.plotly_chart(f_md, use_container_width=True)
        with c2:
            f_s = plot_publisher_share(filtered_df)
            if f_s:
                st.plotly_chart(f_s, use_container_width=True)