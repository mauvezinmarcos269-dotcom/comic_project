import re
from core.visualization.charts import plot_time_series_trend

class ComicAgent:
    def __init__(self, df):
        self.df = df
        
    def process_query(self, query):
        q = query.lower().strip()
        if not q: return "", None
        
        if "十年" in q and ("排名" in q or "前" in q or "特指" in q):
            from core.features.advanced_analytics import get_special_decade_ranking
            ranking, special_notes = get_special_decade_ranking(self.df)
            reply = "🏆 **2010-2019 十年销量 TOP 10 榜单**\n\n"
            for i, (title, sales) in enumerate(ranking.items(), 1):
                reply += f"{i}. 《{title}》 - {sales:,.0f} 册\n"
            
            if special_notes:
                reply += "\n🎯 **特别关注 IP 追踪结果**：\n"
                for title, sales in special_notes:
                    reply += f"- 重点提及的 《{title}》 累计销量达到 {sales:,.0f} 册。\n"
            return reply, None

        if "marvel" in q and "dc" in q:
            comp = self.df[self.df["Studio/Pub"].str.lower().isin(["marvel", "dc"])].groupby("Studio/Pub")["Unit Sales"].mean()
            reply = "📊 **Marvel vs DC 巅峰对决**\n\n"
            for pub, val in comp.items():
                reply += f"• {pub} 平均销量: {val:,.0f} 册\n"
            return reply, None
            
        if "大盘" in q or "走势" in q or "时间序列" in q:
            fig = plot_time_series_trend(self.df)
            return "📈 为您生成了美漫行业历史销量时间序列走势：", fig
            
        if re.search(r'(最高|top|前)\s*(\d+)?', q):
            match = re.search(r'(\d+)', q)
            n = int(match.group(1)) if match else 5
            top = self.df.nlargest(min(n, 20), "Unit Sales")[["Title", "Studio/Pub", "Unit Sales"]]
            reply = f"🔥 **历史单期销量 Top {n}**\n\n"
            for i, (_, row) in enumerate(top.iterrows(), 1):
                reply += f"{i}. 《{row['Title']}》 ({row['Studio/Pub']}) - {row['Unit Sales']:,.0f} 册\n"
            return reply, None
            
        return "🤖 我是美漫数据智能助手。您可以问我：'十年销量前十是谁'、'大盘历史走势' 或 'Marvel和DC谁厉害'。", None

def ask_agent(query, df):
    agent = ComicAgent(df)
    return agent.process_query(query)