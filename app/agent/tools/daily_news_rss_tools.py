# app/agent/tools/daily_news_rss_tool.py

import feedparser
from datetime import datetime, date, timezone
from typing import Optional
import requests
import re
import json
from datapizza.tools import tool


# Feed RSS gratuiti delle principali testate italiane
RSS_SOURCES = {
    "primocanale": {
        "url": "https://www.primocanale.it/rss.xml",
        "name": "Primocanale"
    },
    "genova24": {
        "url": "https://www.genova24.it/feed",
        "name": "Genova24"
    },
    "ligurianotizie": {
        "url": "https://www.ligurianotizie.it/feed/",
        "name": "Liguria Notizie"
    },
    "ivg": {
        "url": "https://www.ivg.it/feed/",
        "name": "IVG.it"
    },
    "ansa": {
        "url": "https://www.ansa.it/sito/ansait_rss.xml",
        "name": "ANSA"
    },
    "repubblica": {
        "url": "https://www.repubblica.it/rss/homepage/rss2.0.xml", 
        "name": "La Repubblica"
    },
    "corriere": {
        "url": "https://xml2.corriereobjects.it/rss/homepage.xml",
        "name": "Corriere della Sera"
    },
    "gazzetta": {
        "url": "https://www.gazzetta.it/rss/home.xml",
        "name": "Gazzetta dello Sport"
    },
    "sole24ore": {
        "url": "https://www.ilsole24ore.com/rss/notizie.xml",
        "name": "Il Sole 24 Ore"
    },
    "agi": {
        "url": "https://www.agi.it/rss",
        "name": "AGI"
    },
    "adnkronos": {
        "url": "https://www.adnkronos.com/rss/homepage.xml",
        "name": "Adnkronos"
    }
}


def _parse_date(date_string: str) -> Optional[date]:
    """Parse della data da diversi formati RSS"""
    if not date_string:
        return None
        
    try:
        # Prova diversi formati comuni nei feed RSS
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",        # ISO 8601
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                if parsed_date.tzinfo is None:
                    # Assume GMT se non c'è timezone
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                return parsed_date.date()
            except ValueError:
                continue
                
        return None
    except Exception:
        return None


def _is_today(article_date: Optional[date]) -> bool:
    """Verifica se la data dell'articolo è oggi"""
    if not article_date:
        return False
    return article_date == date.today()


def _matches_keywords(text: str, keywords: str) -> bool:
    """Verifica se il testo contiene le keyword"""
    if not keywords:
        return True
        
    text_lower = text.lower()
    keywords_lower = keywords.lower()
    
    # Cerca tutte le parole chiave (AND logic)
    return all(keyword.strip() in text_lower for keyword in keywords_lower.split())


@tool
def daily_news_rss_tools(keywords: str = "", sources: str = "", max_results: int = 10) -> str:
    """Cerca notizie italiane pubblicate OGGI da fonti RSS gratuite.
    
    Args:
        keywords: Parole chiave da cercare nei titoli/contenuti (opzionale)
        sources: Lista fonti separate da virgola (ansa,repubblica,corriere,gazzetta,sole24ore,agi,adnkronos) - se vuoto usa tutte
        max_results: Numero massimo di risultati da restituire (default: 10, max: 50)
    
    Returns:
        JSON string con le notizie trovate per oggi
    """
    
    # Parse dei parametri
    if sources:
        source_list = [s.strip() for s in sources.split(",")]
    else:
        source_list = list(RSS_SOURCES.keys())
    
    max_results = min(max(1, max_results), 50)  # Limita tra 1 e 50
    
    today = date.today()
    all_results = []
    
    for source in source_list:
        if source not in RSS_SOURCES:
            continue
            
        try:
            # Scarica e parse del feed RSS
            response = requests.get(
                RSS_SOURCES[source]["url"], 
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                # Estrai la data di pubblicazione
                pub_date = None
                
                if hasattr(entry, 'published'):
                    pub_date = _parse_date(entry.published)
                elif hasattr(entry, 'updated'):
                    pub_date = _parse_date(entry.updated)
                elif hasattr(entry, 'pubDate'):
                    pub_date = _parse_date(entry.pubDate)
                
                # Verifica che sia di oggi
                if not _is_today(pub_date):
                    continue
                
                # Preparazione del testo per la ricerca keywords
                title = getattr(entry, 'title', '')
                description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                
                # Rimuovi tag HTML dalla descrizione
                if description:
                    description = re.sub('<[^<]+?>', '', description).strip()
                
                search_text = f"{title} {description}"
                
                # Filtra per keywords se specificate
                if _matches_keywords(search_text, keywords):
                    all_results.append({
                        "title": title,
                        "description": description[:200] + "..." if len(description) > 200 else description,
                        "link": getattr(entry, 'link', ''),
                        "source": RSS_SOURCES[source]["name"],
                        "published": getattr(entry, 'published', 'N/A'),
                        "pub_date": pub_date.isoformat() if pub_date else None
                    })
                    
        except Exception as e:
            # Log dell'errore ma continua con altre fonti
            continue
    
    # Ordina per data di pubblicazione (più recenti prima)
    all_results.sort(key=lambda x: x['pub_date'] if x['pub_date'] else '', reverse=True)
    
    # Limita i risultati
    results = all_results[:max_results]
    
    # Restituisce JSON per compatibilità con datapizza
    return json.dumps({
        "search_date": today.isoformat(),
        "keywords": keywords if keywords else "tutte le notizie",
        "sources_searched": source_list,
        "total_found": len(all_results),
        "results_returned": len(results),
        "articles": results
    }, ensure_ascii=False, indent=2)


# Per testare il tool in locale
if __name__ == "__main__":
    # Test base
    print("=== Test senza filtri ===")
    result = daily_news_rss_tools()
    print(result)
    
    # Test con keywords
    print("\n=== Test con keywords 'governo' ===")
    result = daily_news_rss_tools(keywords="governo")
    print(result)
    
    # Test con fonte specifica
    print("\n=== Test solo ANSA ===")
    result = daily_news_rss_tools(sources="ansa", max_results=5)
    print(result)
