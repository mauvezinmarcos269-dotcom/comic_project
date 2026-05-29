import requests
from config import COMICVINE_API_KEY
from utils.retry_handler import retry_request

HEADERS = {
    "User-Agent": "ComicResearchBot"
}


def fetch_comicvine_data(title, issue):
    query = f"{title} #{issue}"

    url = (
        "https://comicvine.gamespot.com/api/search/"
        f"?api_key={COMICVINE_API_KEY}"
        "&format=json"
        "&resources=issue"
        f"&query={query}"
    )

    data = retry_request(url, headers=HEADERS)

    if not data:
        return None

    if data.get("number_of_total_results", 0) == 0:
        return None

    result = data["results"][0]

    writer_names = []
    artist_names = []

    for person in result.get("person_credits", []):
        role = person.get("role", "").lower()

        if "writer" in role:
            writer_names.append(person["name"])

        if "artist" in role or "penciler" in role:
            artist_names.append(person["name"])

    characters = [
        c["name"]
        for c in result.get("character_credits", [])[:5]
    ]

    return {
        "writer": ", ".join(writer_names),
        "artist": ", ".join(artist_names),
        "main_character": ", ".join(characters),
        "release_year": result.get("cover_date", "")[:4],
        "description": result.get("deck", "")
    }