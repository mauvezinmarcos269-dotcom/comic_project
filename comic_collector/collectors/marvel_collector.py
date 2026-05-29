import requests


def fetch_marvel_data(title):
    """
    使用非官方 Marvel Metadata API
    """

    try:

        url = (
            "https://marvel.emreparker.com/v1/search/issues"
            f"?q={title}"
        )

        response = requests.get(url, timeout=20)

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        comic = results[0]

        creators = comic.get("creators", [])

        writers = []
        artists = []

        for creator in creators:

            role = creator.get("role", "").lower()

            if "writer" in role:
                writers.append(creator["name"])

            if (
                "artist" in role
                or "penciler" in role
                or "inker" in role
            ):
                artists.append(creator["name"])

        return {

            "marvel_writer":
                ", ".join(writers),

            "marvel_artist":
                ", ".join(artists),

            "series":
                comic.get("series_name", ""),

            "issue_number":
                comic.get("issue_number", ""),

            "description":
                comic.get("description", "")
        }

    except Exception as e:

        print("Marvel Metadata Error:", e)

        return None