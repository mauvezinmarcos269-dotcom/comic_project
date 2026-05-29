import pandas as pd
import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from tqdm import tqdm

# ComicVine
from collectors.comicvine_collector import (
    fetch_comicvine_data
)

# Awards
from collectors.award_detector import (
    detect_awards
)

# Semantic AI
from collectors.semantic_tagger import (
    generate_semantic_tags
)

# Config
from config import (
    INPUT_FILE,
    OUTPUT_FILE,
    MAX_CONCURRENT_REQUESTS
)

# Logger
from utils.logger import logger


# ==========================================
# 读取销量数据
# ==========================================

print("=" * 60)
print("正在读取销量数据...")
print("=" * 60)

df = pd.read_excel(INPUT_FILE)

print(f"成功读取 {len(df)} 条数据")


# ==========================================
# 新字段
# ==========================================

NEW_COLUMNS = [

    "Writer",
    "Artist",
    "Awards",
    "Main_Character",

    "Semantic_Tags",

    "Comic_Type",
    "Hero_Type",
    "Universe",
    "Franchise"
]

for col in NEW_COLUMNS:

    if col not in df.columns:

        df[col] = ""


# ==========================================
# 单条处理函数
# ==========================================

def process_comic(row):

    try:

        # ==================================
        # 基础字段
        # ==================================

        title = str(
            row.get("title", "")
        ).strip()

        issue = str(
            row.get("issue", "")
        ).strip()

        publisher = str(
            row.get("publisher", "")
        ).strip()

        logger.info(
            f"开始处理: {title} #{issue}"
        )

        # ==================================
        # 默认值
        # ==================================

        writer = "Unknown"

        artist = "Unknown"

        main_character = "Unknown"

        # ==================================
        # ComicVine 数据
        # ==================================

        comicvine = fetch_comicvine_data(
            title,
            issue
        )

        if comicvine:

            writer = comicvine.get(
                "writer",
                "Unknown"
            )

            artist = comicvine.get(
                "artist",
                "Unknown"
            )

            main_character = comicvine.get(
                "main_character",
                "Unknown"
            )

        # ==================================
        # Awards
        # ==================================

        awards = detect_awards(
            title
        )

        if not awards:

            awards = "None"

        # ==================================
        # AI 语义分类
        # ==================================

        semantic_data = (
            generate_semantic_tags(
                title
            )
        )

        semantic_tags = semantic_data.get(
            "Semantic_Tags",
            "General Comic"
        )

        comic_type = semantic_data.get(
            "Comic_Type",
            "Unknown"
        )

        hero_type = semantic_data.get(
            "Hero_Type",
            "Unknown"
        )

        universe = semantic_data.get(
            "Universe",
            "Unknown"
        )

        franchise = semantic_data.get(
            "Franchise",
            "Unknown"
        )

        # ==================================
        # Publisher 补充 Universe
        # ==================================

        if universe == "Unknown":

            if "marvel" in publisher.lower():

                universe = "Marvel"

            elif "dc" in publisher.lower():

                universe = "DC"

        # ==================================
        # Main Character 自动修复
        # ==================================

        if (
            main_character == "Unknown"
            and franchise != "Unknown"
        ):

            main_character = franchise

        logger.info(
            f"完成处理: {title}"
        )

        return {

            "Writer":
                writer,

            "Artist":
                artist,

            "Awards":
                awards,

            "Main_Character":
                main_character,

            "Semantic_Tags":
                semantic_tags,

            "Comic_Type":
                comic_type,

            "Hero_Type":
                hero_type,

            "Universe":
                universe,

            "Franchise":
                franchise
        }

    except Exception as e:

        logger.error(
            f"处理失败: {title} "
            f"错误: {e}"
        )

        return {

            "Writer":
                "Unknown",

            "Artist":
                "Unknown",

            "Awards":
                "None",

            "Main_Character":
                "Unknown",

            "Semantic_Tags":
                "General Comic",

            "Comic_Type":
                "Unknown",

            "Hero_Type":
                "Unknown",

            "Universe":
                "Unknown",

            "Franchise":
                "Unknown"
        }


# ==========================================
# 并发处理
# ==========================================

print("=" * 60)
print("开始并发采集数据...")
print("=" * 60)

results = []

with ThreadPoolExecutor(
    max_workers=MAX_CONCURRENT_REQUESTS
) as executor:

    futures = []

    for _, row in df.iterrows():

        future = executor.submit(
            process_comic,
            row
        )

        futures.append(future)

    for future in tqdm(
        as_completed(futures),
        total=len(futures)
    ):

        result = future.result()

        results.append(result)

        time.sleep(0.1)


# ==========================================
# 写回 DataFrame
# ==========================================

print("=" * 60)
print("正在写入结果...")
print("=" * 60)

for col in NEW_COLUMNS:

    df[col] = [

        r.get(col, "Unknown")

        for r in results
    ]


# ==========================================
# 数据清洗
# ==========================================

print("=" * 60)
print("正在清洗数据...")
print("=" * 60)

# 去重
df.drop_duplicates(inplace=True)

# 缺失值
df.fillna("Unknown", inplace=True)

# 标题清洗
df["title"] = (

    df["title"]

    .astype(str)

    .str.strip()
)

# Writer 清洗
df["Writer"] = (

    df["Writer"]

    .astype(str)

    .str.replace(";", ",")

    .str.strip()
)

# Artist 清洗
df["Artist"] = (

    df["Artist"]

    .astype(str)

    .str.replace(";", ",")

    .str.strip()
)

# Semantic Tags 清洗
df["Semantic_Tags"] = (

    df["Semantic_Tags"]

    .astype(str)

    .str.strip()
)

# Main Character 清洗
df["Main_Character"] = (

    df["Main_Character"]

    .astype(str)

    .str.strip()
)

# Franchise 清洗
df["Franchise"] = (

    df["Franchise"]

    .astype(str)

    .str.strip()
)

# Universe 清洗
df["Universe"] = (

    df["Universe"]

    .astype(str)

    .str.strip()
)

# Comic_Type 清洗
df["Comic_Type"] = (

    df["Comic_Type"]

    .astype(str)

    .str.strip()
)

# Hero_Type 清洗
df["Hero_Type"] = (

    df["Hero_Type"]

    .astype(str)

    .str.strip()
)


# ==========================================
# 排序
# ==========================================

if "sales" in df.columns:

    df = df.sort_values(
        by="sales",
        ascending=False
    )


# ==========================================
# 导出 Excel
# ==========================================

print("=" * 60)
print("正在导出 Excel...")
print("=" * 60)

df.to_excel(

    OUTPUT_FILE,

    index=False
)

print("=" * 60)
print("全部完成！")
print("=" * 60)

print(f"输出文件: {OUTPUT_FILE}")

logger.info(
    "全部数据采集完成"
)


