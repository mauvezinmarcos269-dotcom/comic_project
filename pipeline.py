import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Any

from core.config import INPUT_FILE, OUTPUT_FILE, MAX_CONCURRENT_REQUESTS, ENRICHED_FIELDS
from core.constants import YEAR_COLUMN_CANDIDATES
from core.utils.logger import logger
from core.collectors.comicvine_collector import fetch_comicvine_data
from core.collectors.award_detector import detect_awards
from core.collectors.semantic_tagger import (
    generate_semantic_tags, determine_universe,
    determine_comic_type, determine_publication_status
)
from core.features.character_extractor import extract_character
from core.features.issue_analyzer import issue_bucket
from core.features.feature_utils import apply_industry_author_fallbacks


def _find_year_value(row: pd.Series) -> Any:
    """
    从行数据中动态查找年份值，兼容 'Release Year' / 'Release_Year' / 'Year' 等列名。
    修复：原代码硬编码 row.get("Release Year", ...) 导致其他列名时取不到年份。
    """
    for col in YEAR_COLUMN_CANDIDATES:
        val = row.get(col)
        if val is not None:
            return val
    return None


def process_comic_row(idx: int, row: pd.Series) -> tuple[int, dict[str, Any]]:
    """
    处理单行漫画数据，返回索引和富化结果字典。
    
    Args:
        idx: 行索引（int 类型）
        row: 数据行（pd.Series）
    
    Returns:
        tuple: (索引, 富化结果字典)
    """
    try:
        title = str(row.get("Title", row.get("title", ""))).strip()
        issue = str(row.get("Issue", row.get("issue", "1"))).strip()
        # 修复：动态查找年份，不再硬编码 "Release Year"
        year = _find_year_value(row)

        api_data = fetch_comicvine_data(title, issue, year) or {}

        writer = api_data.get("Writer", "Unknown")
        artist = api_data.get("Artist", "Unknown")
        writer, artist = apply_industry_author_fallbacks(title, writer, artist)

        main_char = api_data.get("Main_Character", "Unknown")
        franchise = api_data.get("Franchise", "Unknown")
        if main_char == "Unknown":
            main_char = franchise if franchise != "Unknown" else title

        writer_source = api_data.get(
            "Writer_Source", "ComicVine" if writer != "Unknown" else "Unknown"
        )
        artist_source = api_data.get(
            "Artist_Source", "ComicVine" if artist != "Unknown" else "Unknown"
        )

        return idx, {
            "Writer": writer,
            "Artist": artist,
            "Writer_Source": writer_source,
            "Artist_Source": artist_source,
            "Awards": detect_awards(title),
            "Main_Character": main_char,
            "Semantic_Tags": generate_semantic_tags(title),
            "Comic_Type": determine_comic_type(title),
            "Publication_Status": determine_publication_status(title),
            "Universe": determine_universe(title),
            "Franchise": franchise,
            "Character": extract_character(title),
            "Issue_Group": issue_bucket(issue),
        }
    except Exception as e:
        logger.error(f"行[{idx}] 处理失败: {e}")
        return idx, {}


def run_pipeline() -> None:
    """运行数据富化管线主函数"""
    if not INPUT_FILE.exists():
        print(f"❌ 输入文件不存在: {INPUT_FILE}")
        return

    df = pd.read_excel(INPUT_FILE)
    results: dict[int, dict[str, Any]] = {}

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"🚀 启动并发富化管线 (并发数: {MAX_CONCURRENT_REQUESTS})...")

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # 修复：使用 enumerate 获取整数索引，避免 df.iterrows() 索引类型问题
        futures = {}
        for idx, (_, row) in enumerate(df.iterrows()):
            future = executor.submit(process_comic_row, idx, row)
            futures[future] = idx

        for count, future in enumerate(
            tqdm(as_completed(futures), total=len(futures), desc="富化进度")
        ):
            idx, res = future.result()
            results[idx] = res

            # 断点保存：每处理 50 条保存一次
            if (count + 1) % 50 == 0:
                temp_df = df.copy()
                for col in ENRICHED_FIELDS + ["Issue_Group"]:
                    temp_df[col] = [
                        results.get(i, {}).get(col, "Unknown") for i in temp_df.index
                    ]
                temp_df.to_excel(OUTPUT_FILE, index=False)
                logger.info(f"断点保存完成 ({count + 1}/{len(futures)})")

    # 富化结果写入原始 DataFrame
    for col in ENRICHED_FIELDS + ["Issue_Group"]:
        df[col] = [results.get(i, {}).get(col, "Unknown") for i in range(len(df))]

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ 富化完成！输出文件: {OUTPUT_FILE}")

    # 全局聚类，固化 ML 结果后再次写入
    try:
        from core.features.clustering import perform_advanced_clustering
        print("🧠 正在执行全局 PCA 与 KMeans 聚类...")
        df = perform_advanced_clustering(df)
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"✅ 富化与聚类完成！输出文件: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"全局聚类失败，跳过该步骤: {e}")
        print("⚠️ 全局聚类失败，已跳过，仅保存富化结果。")


if __name__ == "__main__":
    run_pipeline()