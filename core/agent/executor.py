import pandas as pd
from dataclasses import dataclass
from typing import Any
import json
from core.visualization.charts import (
    plot_time_series_trend, plot_marvel_vs_dc_trend, plot_publisher_share,
    plot_rating_vs_sales, plot_correlation_heatmap, plot_pca_clusters,
    plot_word_freq, plot_decade_top10, plot_top_creators
)
from core.features.advanced_analytics import (
    perform_pca_clustering, perform_regression, extract_title_keywords, get_special_decade_ranking
)

@dataclass
class RouterResult:
    answer: str
    chart: Any | None
    evidence: pd.DataFrame | None
    route: dict[str, Any]

def safe_columns(df: pd.DataFrame, desired_cols: list[str]) -> list[str]:
    return [c for c in desired_cols if c in df.columns]

def execute_local_module(route: dict[str, Any], question: str, df: pd.DataFrame, client: Any) -> RouterResult:
    module = route.get("module", "generic_qa")
    params = route.get("params", {})
    
    notice = "提示：由于大模型未连接，已切换至本地匹配模式。\n\n" if "本地" in route.get("reason", "") else ""

    if module == "time_series":
        fig = plot_time_series_trend(df)
        return RouterResult(notice + "已生成行业销量的时间序列走势图。", fig, None, route)

    if module == "publisher_share":
        fig = plot_publisher_share(df)
        evidence = df["Studio/Pub"].value_counts().reset_index() if "Studio/Pub" in df.columns else pd.DataFrame()
        if not evidence.empty: evidence.columns = ["出版商", "收录期刊数"]
        return RouterResult(notice + "已生成主要出版商市场份额占比图。", fig, evidence.head(10), route)

    if module == "correlation":
        fig = plot_correlation_heatmap(df)
        return RouterResult(notice + "已生成数值特征的相关性热力图。", fig, None, route)

    if module == "marvel_dc":
        if "Studio/Pub" not in df.columns:
            return RouterResult("缺少出版商字段，无法对比。", None, None, route)
        publisher = df["Studio/Pub"].astype(str).str.lower()
        sub = df[publisher.str.contains("marvel|dc", na=False)].copy()
        evidence = sub.groupby("Studio/Pub")["Unit Sales"].agg(["count", "sum", "mean"]).reset_index() if "Unit Sales" in df.columns else pd.DataFrame()
        fig = plot_marvel_vs_dc_trend(df)
        return RouterResult(notice + "已生成 Marvel 与 DC 的对比分析图。", fig, evidence, route)

    if module == "rating_sales":
        fig = plot_rating_vs_sales(df)
        return RouterResult(notice + "已生成评分与销量的散点关系图。", fig, None, route)

    if module == "pca_cluster":
        pca_df = perform_pca_clustering(df, n_clusters=4)
        if pca_df is None: return RouterResult("有效数值数据不足，无法进行 PCA 聚类。", None, None, route)
        fig = plot_pca_clusters(pca_df)
        display_cols = safe_columns(pca_df, ["Title", "Studio/Pub", "Unit Sales", "Price", "Cluster"])
        return RouterResult(notice + "已完成 K-Means 聚类和 PCA 降维分析。", fig, pca_df[display_cols].head(15), route)

    if module == "regression":
        reg_df, summary_str = perform_regression(df)
        if reg_df is None: return RouterResult("价格或销量样本不足，跳过回归分析。", None, None, route)
        return RouterResult(notice + "已完成价格与销量的 OLS 回归分析。", None, reg_df[["Price", "Unit Sales", "Predicted_Sales"]].head(15), route)

    if module == "keyword":
        evidence = extract_title_keywords(df)
        fig = plot_word_freq(evidence)
        return RouterResult(notice + "已提取标题高频词汇。", fig, evidence, route)

    if module == "decade_top10":
        ranking, special_notes = get_special_decade_ranking(df)
        fig = plot_decade_top10(df)
        ans = notice + "已生成近十年销量系列总榜 Top 10。"
        return RouterResult(ans, fig, pd.DataFrame(list(ranking.items()), columns=["系列名称", "累计总销量"]), route)

    if module == "creator_top":
        fig = plot_top_creators(df)
        return RouterResult(notice + "已生成主要创作者销量排行。", fig, None, route)

    if module == "grouped_stats":
        groupby = params.get("groupby", "Studio/Pub")
        value = params.get("value", "Unit Sales")
        top_n = min(int(params.get("top_n", 10)), 50)
        
        if groupby not in df.columns or value not in df.columns:
            return RouterResult(f"缺少统计字段 {groupby}/{value}。", None, None, route)
            
        evidence = df.groupby(groupby)[value].agg(["sum", "mean", "count"]).reset_index()
        sort_col = next((m for m in ["sum", "mean", "count"] if m in evidence.columns), evidence.columns[-1])
        evidence = evidence.sort_values(sort_col, ascending=False).head(top_n)
        return RouterResult(notice + f"已按 {groupby} 完成分组统计。", None, evidence, route)

    if module == "top_sales":
        top_n = min(int(params.get("top_n", 10)), 50)
        title_col = "Norm_Title" if "Norm_Title" in df.columns else "Title"
        if "Unit Sales" not in df.columns: return RouterResult("缺少销量特征列。", None, None, route)
        evidence = df.groupby([title_col, "Studio/Pub"])["Unit Sales"].sum().reset_index()
        evidence = evidence.sort_values("Unit Sales", ascending=False).head(top_n)
        return RouterResult(notice + f"已提取全局销量排名前 {top_n} 位的系列。", None, evidence, route)

    if module == "generic_qa" or client is None:
        if "raw_content" in route: return RouterResult(notice + str(route["raw_content"]), None, None, route)
        if client is None:
            ans = notice + f"当前过滤数据集共 `{len(df):,}` 行。请输入包含“走势”、“占比”、“相关性”或“聚类”等词汇调用图表。"
            return RouterResult(ans, None, None, route)
        try:
            sample = df.sample(min(5, len(df)), random_state=42).to_dict(orient="records")
            system_msg = "你是一个美漫数据分析助手，请基于样本简要回答问题。"
            ans_dict = client.chat_json([
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"数据抽样: {sample}\n问题: {question}"}
            ])
            ans_text = ans_dict.get("raw_content", json.dumps(ans_dict, ensure_ascii=False)) if isinstance(ans_dict, dict) else str(ans_dict)
            return RouterResult(notice + ans_text, None, None, route)
        except Exception:
            return RouterResult("请求超时。当前数据总计 `{len(df):,}` 条，建议尝试基础统计查询。", None, None, route)

    return RouterResult(notice + f"已执行分析模块 {module}。", None, None, route)