KNOWN_AWARD_WINNERS = {
    "watchmen": "Hugo Award",
    "守望者": "Hugo Award",
    "maus": "Pulitzer Prize",
    "鼠族": "Pulitzer Prize",
    "sandman": "World Fantasy Award",
    "沙人": "World Fantasy Award",
    "marvels": "Harvey Award",
    "惊奇故事": "Harvey Award",
    "saga": "Eisner Award",
    "传奇": "Eisner Award"
}

def detect_awards(title):
    """支持中英双语的奖项自动检测 + 去重"""
    t = str(title).lower()
    found = [award for kw, award in KNOWN_AWARD_WINNERS.items() if kw in t]
    
    # 去重保持顺序
    distinct_found = []
    for award in found:
        if award not in distinct_found:
            distinct_found.append(award)
            
    return ", ".join(distinct_found) if distinct_found else "None"
