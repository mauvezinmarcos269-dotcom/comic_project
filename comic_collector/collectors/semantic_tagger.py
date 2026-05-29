TEAM_KEYWORDS = [

    "Avengers",
    "X-Men",
    "Justice League",
    "Teen Titans",
    "Fantastic Four",
    "Guardians",
    "Suicide Squad",
    "Defenders",
    "Inhumans",
    "Champions",
    "Legion"
]

SOLO_KEYWORDS = [

    "Batman",
    "Spider-Man",
    "Superman",
    "Thor",
    "Iron Man",
    "Hulk",
    "Venom",
    "Deadpool",
    "Wolverine",
    "Daredevil",
    "Moon Knight",
    "Flash",
    "Green Lantern",
    "Aquaman",
    "Joker",
    "Punisher"
]

EVENT_KEYWORDS = [

    "Civil War",
    "Secret Wars",
    "Crisis",
    "Infinite",
    "War of",
    "Dark Nights",
    "King in Black",
    "Metal",
    "Siege",
    "Annihilation"
]

COSMIC_KEYWORDS = [

    "Guardians",
    "Nova",
    "Silver Surfer",
    "Galactus",
    "Thanos",
    "Annihilation"
]

HORROR_KEYWORDS = [

    "Venom",
    "Carnage",
    "Hellblazer",
    "Spawn",
    "Blade"
]

MUTANT_KEYWORDS = [

    "X-Men",
    "Wolverine",
    "Mutant",
    "X-Force",
    "X-Factor"
]


def generate_semantic_tags(title):

    """
    生成高级语义标签
    """

    title_lower = title.lower()

    tags = set()

    comic_type = "Unknown"

    hero_type = "Unknown"

    universe = "Unknown"

    franchise = "Unknown"

    # =========================
    # Team Book
    # =========================

    for keyword in TEAM_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Team Book")

            comic_type = "Team Series"

            hero_type = "Team"

            franchise = keyword

    # =========================
    # Solo Hero
    # =========================

    for keyword in SOLO_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Solo Hero")

            comic_type = "Solo Series"

            hero_type = "Solo"

            franchise = keyword

    # =========================
    # Event
    # =========================

    for keyword in EVENT_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Event")

            comic_type = "Event"

    # =========================
    # Cosmic
    # =========================

    for keyword in COSMIC_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Cosmic")

    # =========================
    # Horror
    # =========================

    for keyword in HORROR_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Dark")

            tags.add("Horror")

    # =========================
    # Mutant
    # =========================

    for keyword in MUTANT_KEYWORDS:

        if keyword.lower() in title_lower:

            tags.add("Mutant")

    # =========================
    # Marvel / DC
    # =========================

    marvel_keywords = [

        "Spider-Man",
        "Avengers",
        "X-Men",
        "Venom",
        "Thor",
        "Hulk",
        "Iron Man",
        "Deadpool"
    ]

    dc_keywords = [

        "Batman",
        "Superman",
        "Justice League",
        "Flash",
        "Green Lantern",
        "Aquaman",
        "Joker"
    ]

    for keyword in marvel_keywords:

        if keyword.lower() in title_lower:

            universe = "Marvel"

    for keyword in dc_keywords:

        if keyword.lower() in title_lower:

            universe = "DC"

    # =========================
    # 默认标签
    # =========================

    if not tags:

        tags.add("General Comic")

    return {

        "Semantic_Tags":
            ", ".join(tags),

        "Comic_Type":
            comic_type,

        "Hero_Type":
            hero_type,

        "Universe":
            universe,

        "Franchise":
            franchise
    }

