TEAM_KEYWORDS = [
    "avengers", "x-men", "justice league", "teen titans", "fantastic four", "guardians", "suicide squad",
    "复仇者", "x战警", "正义联盟", "少年泰坦", "神奇四侠", "银河护卫队", "自杀小队"
]
EVENT_KEYWORDS = [
    "civil war", "secret wars", "crisis", "infinite", "war of", "dark nights", "metal", "flashpoint",
    "内战", "秘密战争", "危机", "无限", "战争", "黑暗之夜", "金属", "闪点"
]
COMPLETED_SERIES = [
    "watchmen", "batman who laughs", "v for vendetta", "maus", "sandman", "y the last man", "saga",
    "守望者", "狂笑之蝠", "v字仇杀队", "鼠族", "沙人", "y人", "传奇"
]

def determine_comic_type(title):
    t = str(title).lower()
    if any(x in t for x in COMPLETED_SERIES) or any(x in t for x in EVENT_KEYWORDS):
        return "Limited Series"
    if any(x in t for x in TEAM_KEYWORDS):
        return "Ongoing Team"
    return "Ongoing Solo"

def determine_publication_status(title):
    t = str(title).lower()
    if any(x in t for x in COMPLETED_SERIES):
        return "Completed"
    return "Ongoing"

def generate_semantic_tags(title):
    t = str(title).lower()
    tags = set()
    
    if any(kw in t for kw in ["batman", "蝙蝠侠", "侦探漫画"]) and not any(kw in t for kw in EVENT_KEYWORDS):
        tags.add("Street Level")
    if any(kw in t for kw in ["magic", "demon", "sandman", "spawn", "魔法", "恶魔", "沙人", "再生侠"]):
        tags.add("Supernatural")
    if any(kw in t for kw in ["space", "alien", "guardians", "nova", "太空", "外星人", "银河护卫队", "新星"]):
        tags.add("Cosmic")
        
    if not tags:
        tags.add("Superhero")
        
    return ", ".join(sorted(tags))

def determine_universe(title):
    t = str(title).lower()
    if any(kw in t for kw in ["spider-man", "avengers", "x-men", "iron man", "venom", "蜘蛛侠", "复仇者", "x战警", "钢铁侠", "毒液"]):
        return "Marvel"
    if any(kw in t for kw in ["batman", "superman", "justice league", "flash", "detective comics", "蝙蝠侠", "超人", "正义联盟", "闪电侠", "侦探漫画"]):
        return "DC"
    return "Independent"


