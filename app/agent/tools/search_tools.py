from datapizza.tools import tool
import requests

@tool
def web_search(query: str) -> str:
    """Effettua una ricerca web (DuckDuckGo Instant Answer) e restituisce un breve riassunto con link."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        abstract = data.get("AbstractText") or ""
        related = data.get("RelatedTopics", [])
        lines = []
        if abstract:
            lines.append(abstract)
        count = 0
        for item in related:
            if isinstance(item, dict):
                text = item.get("Text")
                link = item.get("FirstURL")
                if text and link:
                    lines.append(f"- {text} ({link})")
                    count += 1
                    if count >= 5:
                        break
        if not lines:
            return "Nessun risultato utile trovato."
        return "\n".join(lines)
    except Exception as e:
        return f"Errore nella ricerca web: {e}"