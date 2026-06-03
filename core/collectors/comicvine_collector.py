import time
from core.config import COMICVINE_API_KEY, HEADERS, REQUEST_TIMEOUT
from core.utils.retry_handler import retry_request
from core.utils.cache_manager import ComicCache
from core.utils.logger import logger
from data_cleaner import KNOWN_CORRECTIONS 

cache = ComicCache()

def fetch_volume_creators(volume_detail_url):
    """Issue 级创作者缺失时的 Volume 级主创降级爬取机制"""
    if not COMICVINE_API_KEY:
        logger.warning("ComicVine API key is not configured; skipping volume creator fetch")
        return [], []
    if not volume_detail_url:
        return [], []
    try:
        url = f"{volume_detail_url}?api_key={COMICVINE_API_KEY}&format=json"
        v_data = retry_request(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if not v_data or "results" not in v_data:
            return [], []
        
        results = v_data["results"]
        w_names, a_names = [], []
        
        for person in results.get("person_credits", []):
            role = person.get("role", "").lower()
            name = person.get("name", "")
            if "writer" in role:
                w_names.append(name)
            if any(r in role for r in ["artist", "penciler", "inker"]):
                a_names.append(name)
        return w_names, a_names
    except Exception as e:
        logger.error(f"Volume 追溯降级数据补全失败: {e}")
        return [], []

def fetch_comicvine_data(title, issue, release_year=None):
    """从 ComicVine 获取漫画数据，支持智能本地修正、向上容错追溯与高速缓存"""
    clean_title = str(title).strip().lower()
    clean_issue = str(issue).strip()

    # 1. 检查本地已知修正库 (包含匹配映射，提前短路，避免触发远程网络请求)
    matched_correction = None
    for (k_title, k_issue), value in KNOWN_CORRECTIONS.items():
        if k_title in clean_title and k_issue == clean_issue:
            matched_correction = value
            break

    if matched_correction:
        logger.info(f"优先命中本地已知修正数据库: {title} #{issue}")
        return {
            "Writer": matched_correction.get("Writer", "Unknown"),
            "Artist": matched_correction.get("Artist", "Unknown"),
            "Main_Character": matched_correction.get("Main_Character", "Unknown"),
            "Franchise": matched_correction.get("Franchise", "Unknown")
        }

    # 2. 检查高速缓存
    if not COMICVINE_API_KEY:
        logger.warning("ComicVine API key is not configured; skipping remote fetch")
        return None

    cached = cache.get(title, issue, release_year)
    if cached:
        logger.info(f"缓存命中: {title} #{issue}")
        return cached

    # 3. 检索 Issue
    search_url = f"https://comicvine.gamespot.com/api/search/?api_key={COMICVINE_API_KEY}&format=json&resources=issue&query={title}"
    logger.info(f"搜索 API: {title} #{issue}")
    data = retry_request(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    
    if not data or data.get("number_of_total_results", 0) == 0:
        logger.warning(f"API 未检索到实体结果: {title} #{issue}")
        return None

    # 4. 精确匹配刊号和关联加权
    candidates = []
    for item in data.get("results", []):
        api_issue = str(item.get("issue_number", "")).strip()
        if api_issue != clean_issue:
            continue
        
        score = 0
        volume = item.get("volume", {})
        volume_name = volume.get("name", "")
        
        if clean_title in volume_name.lower():
            score += 10
        if release_year:
            cover_date = item.get("cover_date", "")
            if str(release_year) in cover_date:
                score += 20
        candidates.append((score, item))
    
    if not candidates:
        logger.warning(f"刊号未能与 API 列表对齐: {title} #{issue}")
        return None
    
    best = max(candidates, key=lambda x: x[0])[1]
    detail_url = best.get("api_detail_url", "")
    if not detail_url:
        return None
    
    detail_url = f"{detail_url}?api_key={COMICVINE_API_KEY}&format=json"
    detail = retry_request(detail_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if not detail or "results" not in detail:
        return None
    
    result = detail["results"]
    writer_names = []
    artist_names = []
    
    # 5. 解析制作者
    for person in result.get("person_credits", []):
        role = person.get("role", "").lower()
        name = person.get("name", "")
        if "writer" in role:
            writer_names.append(name)
        if any(r in role for r in ["artist", "penciler", "inker"]):
            artist_names.append(name)
            
    # 若发现 Issue 级别的团队为空，执行智能兜底：向父级 Volume 获取
    if not writer_names or not artist_names:
        v_url = result.get("volume", {}).get("api_detail_url")
        if v_url:
            logger.info(f"期刊制作名单空缺，启动 Volume 降级补全机制：{title}")
            v_writers, v_artists = fetch_volume_creators(v_url)
            if not writer_names: writer_names = v_writers
            if not artist_names: artist_names = v_artists

    # 6. 提取前三个主要出场角色
    characters = []
    for char in result.get("character_credits", [])[:3]:
        char_name = char.get("name", "")
        if char_name:
            characters.append(char_name)
    
    volume = result.get("volume", {})
    franchise = volume.get("name", "Unknown")
    
    out = {
        "Writer": "; ".join(writer_names) if writer_names else "Unknown",
        "Artist": "; ".join(artist_names) if artist_names else "Unknown",
        "Main_Character": characters[0] if characters else "Unknown",
        "Franchise": franchise
    }
    
    logger.info(f"API 解析成功: {title} #{issue} -> Writer: {out['Writer'][:20]}")
    cache.set(title, issue, release_year, out)
    return out
