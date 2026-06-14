import re
import pandas as pd
from typing import Any
from core.agent.llm_client import SiliconFlowClient
from core.agent.executor import execute_local_module

def get_lightweight_schema(df: pd.DataFrame) -> list[dict[str, str]]:
    return [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns]

def local_regex_router(question: str) -> dict[str, Any]:
    q = question.lower().strip()
    
    if any(kw in q for kw in ["大盘", "走势", "时间序列", "趋势", "历年"]):
        return {"module": "time_series", "params": {}, "reason": "本地离线硬匹配：时间序列走势图"}
    if any(kw in q for kw in ["漫威", "marvel", "dc", "对决", "对立"]):
        return {"module": "marvel_dc", "params": {}, "reason": "本地离线硬匹配：漫威与DC大盘对比"}
    if any(kw in q for kw in ["份额", "占比", "比例", "结构", "饼图"]):
        return {"module": "publisher_share", "params": {}, "reason": "本地离线硬匹配：出版商市场份额占比"}
    if any(kw in q for kw in ["评分", "散点", "评价"]):
        return {"module": "rating_sales", "params": {}, "reason": "本地离线硬匹配：评分vs销量散点图"}
    if any(kw in q for kw in ["热力图", "相关性", "相关系数", "交叉矩阵"]):
        return {"module": "correlation", "params": {}, "reason": "本地离线硬匹配：多维特征相关性热力图"}
    if any(kw in q for kw in ["聚类", "pca", "降维", "群体", "分类"]):
        return {"module": "pca_cluster", "params": {}, "reason": "本地离线硬匹配：PCA降维聚类分析"}
    if any(kw in q for kw in ["回归", "ols", "拟合", "价格影响"]):
        return {"module": "regression", "params": {}, "reason": "本地离线硬匹配：价格-销量回归分析模型"}
    if any(kw in q for kw in ["词云", "高频词", "关键字", "标题词"]):
        return {"module": "keyword", "params": {}, "reason": "本地离线硬匹配：核心词频深度分析"}
    if any(kw in q for kw in ["十年", "年代", "经典", "2010"]):
        return {"module": "decade_top10", "params": {}, "reason": "本地离线硬匹配：黄金十年Top10里程碑"}
    if any(kw in q for kw in ["作者", "创作者", "编剧", "画家", "画师"]):
        return {"module": "creator_top", "params": {}, "reason": "本地离线硬匹配：核心创作者战绩榜单"}
        
    # 修复：采用更稳健的非捕获组正则，杜绝 top10/TOP10 的解析遗漏
    if any(kw in q for kw in ["排行", "最高", "top", "前10", "前20", "前50", "前100", "销量最高"]):
        match = re.search(r"(?:top|前)\s*(\d+)", q, re.IGNORECASE)
        top_n = int(match.group(1)) if match else 10
        return {"module": "top_sales", "params": {"top_n": top_n}, "reason": "本地离线硬匹配：全局销量大排行"}
        
    return {"module": "generic_qa", "params": {}, "reason": "未命中特定图表组件，自动划归至通用指标统计"}

def route_question(question: str, df: pd.DataFrame, client: SiliconFlowClient) -> dict[str, Any]:
    """智能路由分发中心"""
    schema = get_lightweight_schema(df)
    
    system_prompt = """
你是一个数据分析路由器。请根据用户问题，从下方选定一个最佳模块。
可用模块：
- macro_stats: 总体统计 (均值, 总和等)
- grouped_stats: 分组聚合统计 (如按出版商)
- publisher_share: 饼图-出版商份额
- time_series: 折线图-时间序列销量
- marvel_dc: 漫威与DC专享对比
- rating_sales: 评分与销量散点
- correlation: 数值特征热力图
- pca_cluster: PCA聚类降维
- regression: OLS价格销量回归
- keyword: 标题高频词汇挖掘
- decade_top10: 经典年代销量榜
- creator_top: 创作者排行
- top_sales: 全局历史销量榜
- generic_qa: 其他通用问答

务必只输出 JSON 格式：
{"module": "模块名", "params": {"key": "value"}, "reason": "中文理由"}
"""
    user_prompt = f"字段结构: {schema}\n\n用户提问: {question}"
    
    try:
        return client.chat_json([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
    except Exception as e:
        route = local_regex_router(question)
        route["reason"] = f"在线Agent网关未激活（已平滑触发本地离线硬路由保护图表组件）。异常详情: {str(e)}"
        return route

def ask_with_llm_router(question: str, df: pd.DataFrame, api_key: str, model: str):
    """双轨制入口包装器"""
    try:
        client = SiliconFlowClient(api_key=api_key, model=model)
        route = route_question(question, df, client)
    except ValueError as e:
        client = None
        route = local_regex_router(question)
        route["reason"] = f"系统检测到 API Key 配置存在中文残留或格式乱码，已强制切换至本地离线内核。原因: {str(e)}"
        
    return execute_local_module(route, question, df, client)