import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from core.config import INPUT_FILE, OUTPUT_FILE, MAX_CONCURRENT_REQUESTS, ENRICHED_FIELDS
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

def process_comic_row(idx, row):
    try:
        title = str(row.get("Title", row.get("title", ""))).strip()
        issue = str(row.get("Issue", row.get("issue", "1"))).strip()
        year = row.get("Release Year", row.get("release_year"))
        
        api_data = fetch_comicvine_data(title, issue, year) or {}
        
        writer = api_data.get("Writer", "Unknown")
        artist = api_data.get("Artist", "Unknown")
        writer, artist = apply_industry_author_fallbacks(title, writer, artist)
        
        main_char = api_data.get("Main_Character", "Unknown")
        franchise = api_data.get("Franchise", "Unknown")
        if main_char == "Unknown":
            main_char = franchise if franchise != "Unknown" else title

        writer_source = api_data.get("Writer_Source", "ComicVine" if writer != "Unknown" else "Unknown")
        artist_source = api_data.get("Artist_Source", "ComicVine" if artist != "Unknown" else "Unknown")
        
        return idx, {
            "Writer": writer, "Artist": artist,
            "Writer_Source": writer_source, "Artist_Source": artist_source,
            "Awards": detect_awards(title),
            "Main_Character": main_char,
            "Semantic_Tags": generate_semantic_tags(title),
            "Comic_Type": determine_comic_type(title),
            "Publication_Status": determine_publication_status(title),
            "Universe": determine_universe(title),
            "Franchise": franchise,
            "Character": extract_character(title),
            "Issue_Group": issue_bucket(issue)
        }
    except Exception as e:
        logger.error(f"行[{idx}] 处理失败: {e}")
        return idx, {}

def run_pipeline():
    if not INPUT_FILE.exists():
        print(f"❌ 输入文件不存在: {INPUT_FILE}")
        return
    
    df = pd.read_excel(INPUT_FILE)
    results = {}
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 启动并发富化管线 (并发数: {MAX_CONCURRENT_REQUESTS})...")
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        futures = {executor.submit(process_comic_row, i, r): i for i, r in df.iterrows()}
        
        for count, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="富化进度")):
            idx, res = future.result()
            results[idx] = res
            
            if (count + 1) % 50 == 0:  # 断点保存
                temp_df = df.copy()
                for col in ENRICHED_FIELDS + ["Issue_Group"]:
                    temp_df[col] = [results.get(i, {}).get(col, "Unknown") for i in temp_df.index]
                temp_df.to_excel(OUTPUT_FILE, index=False)
                logger.info(f"断点保存完成 ({count+1}/{len(futures)})")

    # 最终写入
    for col in ENRICHED_FIELDS + ["Issue_Group"]:
        df[col] = [results.get(i, {}).get(col, "Unknown") for i in df.index]
    
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ 富化完成！输出文件: {OUTPUT_FILE}")
       
    # 在输出前执行全局聚类，固化 ML 结果
    try:
        from core.features.clustering import perform_advanced_clustering
        print("🧠 正在执行全局 PCA 与 KMeans 聚类...")
        df = perform_advanced_clustering(df)
    except Exception as e:
        logger.error(f"全局聚类失败，跳过该步骤: {e}")

    # 最终写入
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ 富化与聚类完成！输出文件: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_pipeline()
    