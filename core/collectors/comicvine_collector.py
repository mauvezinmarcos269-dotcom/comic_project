import time
from core.config import COMICVINE_API_KEY, HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, TITLE_TRANSLATIONS, KNOWN_CORRECTIONS
from core.utils.retry_handler import retry_request
from core.utils.cache_manager import ComicCache
from core.utils.logger import logger

cache = ComicCache()

def fetch_volume_creators(volume_detail_url):
    if not COMICVINE_API_KEY or not volume_detail_url:
        return [], []
    try:
        params = {"api_key": COMICVINE_API_KEY, "format": "json"}
        v_data = retry_request(volume_detail_url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
        if not v_data or "results" not in v_data:
            return [], []
        
        w_names, a_names = [], []
        for person in v_data["results"].get("person_credits", []):
            role = person.get("role", "").lower()
            name = person.get("name", "")
            if "writer" in role:
                w_names.append(name)
            if any(r in role for r in ["artist", "penciler", "inker"]):
                a_names.append(name)
        return w_names, a_names
    except Exception as e:
        logger.error(f"Volume 降级失败: {e}")
        return [], []


def fetch_comicvine_data(title, issue, release_year=None):
    clean_title = str(title).strip().lower()
    clean_issue = str(issue).strip()

    # 1. 本地修正短路（最快路径）
    for (k_title, k_issue), value in KNOWN_CORRECTIONS.items():
        if k_title in clean_title and str(k_issue) == clean_issue:
            logger.info(f"本地修正命中: {title} #{issue}")
            value = value.copy()
            value.update({"Writer_Source": "LocalCorrection", "Artist_Source": "LocalCorrection"})
            return value

    # 2. 缓存
    cached = cache.get(title, issue, release_year)
    if cached:
        logger.info(f"缓存命中: {title} #{issue}")
        return cached

    # 3. 标题翻译
    api_query_title = clean_title
    for cn_name, en_name in TITLE_TRANSLATIONS.items():
        if cn_name in clean_title:
            api_query_title = api_query_title.replace(cn_name, en_name.lower()).strip()
            break

    out = None

    # 4. ComicVine API（带最小延迟）
    if COMICVINE_API_KEY:
        try:
            search_url = "https://comicvine.gamespot.com/api/search/"
            params = {
                "api_key": COMICVINE_API_KEY,
                "format": "json",
                "resources": "issue",
                "query": api_query_title
            }
            data = retry_request(search_url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            
            if data and data.get("number_of_total_results", 0) > 0:
                candidates = []
                for item in data.get("results", []):
                    if str(item.get("issue_number", "")).strip() != clean_issue:
                        continue
                    score = 10 if api_query_title in item.get("volume", {}).get("name", "").lower() else 0
                    if release_year and str(release_year) in item.get("cover_date", ""):
                        score += 20
                    candidates.append((score, item))
                
                if candidates:
                    best = max(candidates, key=lambda x: x[0])[1]
                    detail_url = best.get("api_detail_url", "")
                    if detail_url:
                        detail = retry_request(f"{detail_url}?api_key={COMICVINE_API_KEY}&format=json", 
                                             headers=HEADERS, timeout=REQUEST_TIMEOUT)
                        
                        if detail and "results" in detail:
                            result = detail["results"]
                            writer_names = [p.get("name","") for p in result.get("person_credits", []) if "writer" in p.get("role","").lower()]
                            artist_names = [p.get("name","") for p in result.get("person_credits", []) 
                                          if any(r in p.get("role","").lower() for r in ["artist","penciler","inker"])]
                            
                            if not writer_names or not artist_names:
                                v_url = result.get("volume", {}).get("api_detail_url")
                                if v_url:
                                    v_w, v_a = fetch_volume_creators(v_url)
                                    writer_names = writer_names or v_w
                                    artist_names = artist_names or v_a

                            chars = [c.get("name","") for c in result.get("character_credits", [])[:3] if c.get("name")]
                            out = {
                                "Writer": "; ".join(writer_names) if writer_names else "Unknown",
                                "Artist": "; ".join(artist_names) if artist_names else "Unknown",
                                "Main_Character": chars[0] if chars else "Unknown",
                                "Franchise": result.get("volume", {}).get("name", "Unknown"),
                                "Writer_Source": "ComicVine" if writer_names else "Unknown",
                                "Artist_Source": "ComicVine" if artist_names else "Unknown"
                            }
        except Exception as e:
            logger.error(f"ComicVine 异常: {e}")

    # 5. GCD 补偿
    if not out or out.get("Writer") == "Unknown" or out.get("Artist") == "Unknown":
        try:
            from core.collectors.gcd_collector import fetch_gcd_data
            gcd_res = fetch_gcd_data(api_query_title, clean_issue)
            if gcd_res:
                if not out:
                    out = {"Main_Character": "Unknown", "Franchise": gcd_res.get("Franchise", api_query_title)}
                if out.get("Writer") == "Unknown" and gcd_res.get("Writer") != "Unknown":
                    out["Writer"] = gcd_res["Writer"]
                    out["Writer_Source"] = "GCD"
                if out.get("Artist") == "Unknown" and gcd_res.get("Artist") != "Unknown":
                    out["Artist"] = gcd_res["Artist"]
                    out["Artist_Source"] = "GCD"
        except Exception as e:
            logger.error(f"GCD 补偿异常: {e}")

    out = out or {
        "Writer": "Unknown", "Artist": "Unknown", "Main_Character": "Unknown",
        "Franchise": api_query_title, "Writer_Source": "Unknown", "Artist_Source": "Unknown"
    }
    
    cache.set(title, issue, release_year, out)
    return out