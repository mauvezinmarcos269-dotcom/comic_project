from core.config import FALLBACK_CREATORS

def apply_industry_author_fallbacks(title: str, writer: str, artist: str) -> tuple[str, str]:

    t_lower = str(title).lower()
    
    # 待检测的空值集合
    invalid_markers = {"unknown", "none", "nan", ""}
    
    # 定义当前的清理函数
    def is_invalid(val):
        return not val or str(val).lower().strip() in invalid_markers

    # 第一层：尝试从 config 字典中匹配
    for key, creators in FALLBACK_CREATORS.items():
        if key in t_lower:
            if is_invalid(writer):
                writer = creators.get("writer", writer)
            if is_invalid(artist):
                artist = creators.get("artist", artist)
            break

    # 第二层：硬编码兜底（仅针对极少数高频 IP，防止遗漏）
    if is_invalid(writer):
        if "spider-man" in t_lower: writer = "Dan Slott"
        elif "batman" in t_lower: writer = "Scott Snyder"
        elif "superman" in t_lower: writer = "Geoff Johns"
        elif "avengers" in t_lower: writer = "Brian Michael Bendis"
        elif "x-men" in t_lower: writer = "Chris Claremont"
        
    if is_invalid(artist):
        if "spider-man" in t_lower: artist = "Humberto Ramos"
        elif "batman" in t_lower: artist = "Greg Capullo"
        elif "superman" in t_lower: artist = "Gary Frank"
        elif "avengers" in t_lower: artist = "John Romita Jr."
        elif "x-men" in t_lower: artist = "Jim Lee"
            
    return str(writer).strip(), str(artist).strip()