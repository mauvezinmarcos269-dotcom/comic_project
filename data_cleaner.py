import pandas as pd
from core.config import DEFAULT_DATA_FILE, ENRICHED_DATA_FILE

COLUMN_ALIASES = {
    "units": "Rank", "rank": "Rank",
    "title": "Title", "issue": "Issue", "price": "Price",
    "publisher": "Studio/Pub", "studio": "Studio/Pub",
    "sales": "Unit Sales", "Unit_Sales": "Unit Sales",
    "release_year": "Release Year", "Release_Year": "Release Year"
}
NORMALIZED_COLUMN_ALIASES = {
    str(key).strip().lower(): value for key, value in COLUMN_ALIASES.items()
}

KNOWN_CORRECTIONS = {
    ("detective comics", "1000"): {
        "Writer": "Peter J. Tomasi",
        "Artist": "Doug Mahnke",
        "Main_Character": "Batman",
        "Comic_Type": "Ongoing Solo",
        "Publication_Status": "Ongoing",
        "Universe": "DC",
        "Franchise": "Detective Comics"
    }
}

# AI-assisted: 由 AI 辅助优化了字段标准化逻辑，修正了 .str.contains 的模糊匹配调用 [cite: 63, 64]
def clean_text(value, default=""):
    if pd.isna(value):
        return default
    return str(value).strip()

def load_and_clean_comic_data(file_path=None):
    file_path = file_path or (ENRICHED_DATA_FILE if ENRICHED_DATA_FILE.exists() else DEFAULT_DATA_FILE)
    
    df = pd.read_excel(file_path) if str(file_path).endswith('.xlsx') else pd.read_csv(file_path)
    # 统一列名映射
    df = df.rename(columns=lambda x: NORMALIZED_COLUMN_ALIASES.get(clean_text(x).lower(), x))
    df = df.rename(columns=COLUMN_ALIASES)

    df["Title"] = df["Title"].map(clean_text)
    df["Issue"] = df["Issue"].map(lambda value: clean_text(value, "1")) if "Issue" in df.columns else "1"
    df["Studio/Pub"] = df["Studio/Pub"].map(lambda value: clean_text(value, "Independent"))

    df["Unit Sales"] = pd.to_numeric(df["Unit Sales"], errors="coerce").fillna(0).astype(int)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0).astype(float)
    df["Release Year"] = pd.to_numeric(df["Release Year"], errors="coerce").fillna(2026).astype(int)
    
    df["Rating"] = pd.to_numeric(df.get("Rating", pd.NA), errors="coerce")
    df["Page Count"] = pd.to_numeric(df.get("Page Count", pd.NA), errors="coerce")

    enriched_fields = [
        "Writer", "Artist", "Awards", "Main_Character", "Semantic_Tags", 
        "Comic_Type", "Publication_Status", "Universe", "Franchise", "Character"
    ]
    invalid_strs = {"unknown", "none", "nan", "null", "not available", ""}

    for col in enriched_fields:
        if col not in df.columns:
            df[col] = "Not Enriched"
        else:
            missing_mask = df[col].isna()
            df[col] = df[col].map(clean_text)
            normalized = df[col].map(lambda value: clean_text(value).lower())
            mask = normalized.isin(invalid_strs) | missing_mask
            df.loc[mask, col] = "Not Available"

    for (title, issue), corrections in KNOWN_CORRECTIONS.items():
        normalized_title = df["Title"].map(lambda value: clean_text(value).lower())
        mask = (
            normalized_title.str.contains(clean_text(title).lower(), na=False, regex=False) & 
            (df['Issue'] == str(issue))
        )
        for col, value in corrections.items():
            if col in df.columns:
                df.loc[mask, col] = value

    return df
