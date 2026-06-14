# ── 聚类商业标签（顺序即展示优先级）──────────────────────────────────────────
LABEL_ORDER: list[str] = [
    "Blockbuster IP (大IP主线)",
    "Event Comics (独立大事件)",
    "Premium Series (精品限定)",
    "Long Tail (长尾市场)",
]

# ── 聚类数量（必须与 LABEL_ORDER 长度一致）───────────────────────────────────
N_CLUSTERS: int = len(LABEL_ORDER)  # = 4

# ── 每个标签对应的固定展示颜色 ────────────────────────────────────────────────
# 顺序与 LABEL_ORDER 一一对应，改标签名时同步改这里
CLUSTER_COLORS: dict[str, str] = {
    "Blockbuster IP (大IP主线)":  "#1f77b4",
    "Event Comics (独立大事件)":   "#d62728",
    "Premium Series (精品限定)":   "#2ca02c",
    "Long Tail (长尾市场)":        "#ff7f0e",
}

# ── 每个标签的业务描述（用于探针卡片展示）────────────────────────────────────
CLUSTER_DESC: dict[str, str] = {
    "Blockbuster IP (大IP主线)":
        "持续高销量，极长的日常连载周数与历史积累",
    "Event Comics (独立大事件)":
        "单期销量极端爆发突破常规，普遍集中在 #1 创刊号或年度联动节点",
    "Premium Series (精品限定)":
        "发行长度受限，内容评分中位数极高，具备更强的精品艺术属性与客单价",
    "Long Tail (长尾市场)":
        "单刊日常销量处于中下游，但作品基数极其庞大，构成产业的基本长尾盘",
}

# ── 数据清洗：视为无效值的字符串集合（全小写）─────────────────────────────────
INVALID_VALUES: frozenset[str] = frozenset({
    "not available", "not enriched", "unknown",
    "none", "nan", "n/a", "",
})

# ── Release Year 列名候选（按优先级排列）──────────────────────────────────────
YEAR_COLUMN_CANDIDATES: list[str] = [
    "Release Year", "Release_Year", "Year", "release_year",
]