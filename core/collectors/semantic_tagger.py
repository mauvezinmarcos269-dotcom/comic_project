TEAM_KEYWORDS = ["avengers", "x-men", "justice league", "teen titans", "fantastic four", "guardians", "suicide squad"]
EVENT_KEYWORDS = ["civil war", "secret wars", "crisis", "infinite", "war of", "dark nights", "metal", "flashpoint"]
COMPLETED_SERIES = ["watchmen", "batman who laughs", "v for vendetta", "maus", "sandman", "y the last man", "saga"]

# AI-assisted: 彻底解耦连载体量与生命周期，支持精确识别限定剧集与已完结状态
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
    
    if "batman" in t and not any(kw in t for kw in EVENT_KEYWORDS):
        tags.add("Street Level")
    if any(kw in t for kw in ["magic", "demon", "sandman", "spawn"]):
        tags.add("Supernatural")
    if any(kw in t for kw in ["space", "alien", "guardians", "nova"]):
        tags.add("Cosmic")
        
    if not tags:
        tags.add("Superhero")
        
    return ", ".join(sorted(tags))

def determine_universe(title):
    t = str(title).lower()
    if any(kw in t for kw in ["spider-man", "avengers", "x-men", "iron man", "venom"]):
        return "Marvel"
    if any(kw in t for kw in ["batman", "superman", "justice league", "flash"]):
        return "DC"
    return "Independent"


