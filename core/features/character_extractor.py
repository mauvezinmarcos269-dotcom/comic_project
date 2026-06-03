import re

CHAR_PATTERNS = {
    "Batman": r"batman|dark knight",
    "Spider-Man": r"spider[- ]?man|peter parker",
    "Superman": r"superman|man of steel",
    "X-Men": r"x[- ]?men",
    "Avengers": r"avengers",
    "Venom": r"venom",
    "Deadpool": r"deadpool",
    "Thor": r"thor",
    "Flash": r"flash",
    "Joker": r"joker",
    "Star Wars": r"star wars",
    "Spawn": r"spawn",
    "Justice League": r"justice league",
    "Iron Man": r"iron man",
    "Wolverine": r"wolverine|logan"
}

def extract_character(title):
    t = str(title).lower()
    for char, pat in CHAR_PATTERNS.items():
        if re.search(pat, t):
            return char
    return "Other"