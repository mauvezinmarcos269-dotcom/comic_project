KNOWN_AWARD_WINNERS = {
    "watchmen": "Hugo Award",
    "maus": "Pulitzer Prize",
    "sandman": "World Fantasy Award",
    "marvels": "Harvey Award",
    "saga": "Eisner Award"
}

def detect_awards(title):
    t = str(title).lower()
    found = [award for kw, award in KNOWN_AWARD_WINNERS.items() if kw in t]
    return ", ".join(found) if found else "None"

