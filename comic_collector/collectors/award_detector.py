AWARD_MAP = {
    "Saga": "Eisner Award",
    "Watchmen": "Hugo Award",
    "Sandman": "World Fantasy Award",
    "Maus": "Pulitzer Prize",
    "Monstress": "Harvey Award"
}


def detect_awards(title):
    awards = []

    for keyword, award in AWARD_MAP.items():
        if keyword.lower() in title.lower():
            awards.append(award)

    return ", ".join(awards)