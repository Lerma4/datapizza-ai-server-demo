import feedparser
from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
import requests
from datapizza.tools import Tool
import re


class DailyNewsRSSTool(Tool):
    """Tool gratuito per cercare notizie italiane pubblicate oggi da fonti RSS"""
    
    def __init__(self):
        # Feed RSS gratuiti delle principali testate italiane
        self.rss_sources = {
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
    
    def name(self) -> str:
        return "daily_news_rss_search"
        
    def description(self) -> str:
        return """Cerca notizie italiane pubblicate OGGI (nelle ultime 24 ore) da fonti RSS gratuite.
        Parametri:
        - keywords: parole chiave da cercare nei titoli/contenuti (opzionale)
        - sources: lista fonti specifiche (ansa, repubblica, corriere, gazzetta, sole24ore, agi, adnkronos)
        - max_results: numero massimo di risultati da restituire (default: 10)"""
    
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Parole chiave da cercare nei titoli e descrizioni (opzionale)"
                },
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["ansa", "repubblica", "corriere", "gazzetta", "sole24ore", "agi", "adnkronos"]
                    },
                    "description": "Fonti specifiche da includere (se vuoto, cerca in tutte)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Numero massimo di risultati da restituire",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                }
            }
        }
    
    def _parse_date(self, date_string: str) -> Optional[date]:
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
    
    def _is_today(self, article_date: Optional[date]) -> bool:
        """Verifica se la data dell'articolo è oggi"""
        if not article_date:
            return False
        return article_date == date.today()
    
    def _matches_keywords(self, text: str, keywords: str) -> bool:
        """Verifica se il testo contiene le keyword"""
        if not keywords:
            return True
            
        text_lower = text.lower()
        keywords_lower = keywords.lower()
        
        # Cerca tutte le parole chiave (AND logic)
        return all(keyword.strip() in text_lower for keyword in keywords_lower.split())
    
    def run(self, keywords: str = "", sources: Optional[List[str]] = None, max_results: int = 10) -> str:
        if not sources:
            sources = list(self.rss_sources.keys())
        
        today = date.today()
        all_results = []
        
        for source in sources:
            if source not in self.rss_sources:
                continue
                
            try:
                # Scarica e parse del feed RSS
                response = requests.get(
                    self.rss_sources[source]["url"], 
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
                )
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries:
                    # Estrai la data di pubblicazione
                    pub_date = None
                    
                    if hasattr(entry, 'published'):
                        pub_date = self._parse_date(entry.published)
                    elif hasattr(entry, 'updated'):
                        pub_date = self._parse_date(entry.updated)
                    elif hasattr(entry, 'pubDate'):
                        pub_date = self._parse_date(entry.pubDate)
                    
                    # Verifica che sia di oggi
                    if not self._is_today(pub_date):
                        continue
                    
                    # Preparazione del testo per la ricerca keywords
                    title = getattr(entry, 'title', '')
                    description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                    
                    # Rimuovi tag HTML dalla descrizione
                    if description:
                        description = re.sub('<[^<]+?>', '', description).strip()
                    
                    search_text = f"{title} {description}"
                    
                    # Filtra per keywords se specificate
                    if self._matches_keywords(search_text, keywords):
                        all_results.append({
                            "title": title,
                            "description": description[:200] + "..." if len(description) > 200 else description,
                            "link": getattr(entry, 'link', ''),
                            "source": self.rss_sources[source]["name"],
                            "published": getattr(entry, 'published', 'N/A'),
                            "pub_date": pub_date
                        })
                        
            except Exception as e:
                # Log dell'errore ma continua con altre fonti
                print(f"Errore nel processare {source}: {str(e)}")
                continue
        
        # Ordina per data di pubblicazione (più recenti prima)
        all_results.sort(key=lambda x: x['pub_date'] if x['pub_date'] else date.min, reverse=True)
        
        # Limita i risultati
        results = all_results[:max_results]
        
        if results:
            search_info = f"Keyword: '{keywords}'" if keywords else "Tutte le notizie"
            sources_info = f"Fonti: {', '.join(sources)}" if len(sources) < len(self.rss_sources) else "Tutte le fonti"
            
            output = f"🗞️ NOTIZIE DI OGGI ({today.strftime('%d/%m/%Y')})\n"
            output += f"📊 {search_info} | {sources_info}\n"
            output += f"📈 Trovate {len(results)} notizie su {len(all_results)} totali\n\n"
            
            for i, article in enumerate(results, 1):
                output += f"{i}. **{article['title']}**\n"
                output += f"   📰 {article['source']}\n"
                if article['description']:
                    output += f"   📝 {article['description']}\n"
                output += f"   🔗 {article['link']}\n"
                output += f"   ⏰ {article['published']}\n\n"
            
            return output
        else:
            search_msg = f" con keywords '{keywords}'" if keywords else ""
            return f"❌ Nessuna notizia trovata per oggi ({today.strftime('%d/%m/%Y')}){search_msg} dalle fonti specificate."


# Per testare il tool in locale
if __name__ == "__main__":
    tool = DailyNewsRSSTool()
    
    # Test base
    print("=== Test senza filtri ===")
    result = tool.run()
    print(result)
    
    # Test con keywords
    print("\n=== Test con keywords 'governo' ===")
    result = tool.run(keywords="governo")
    print(result)
    
    # Test con fonte specifica
    print("\n=== Test solo ANSA ===")
    result = tool.run(sources=["ansa"], max_results=5)
    print(result)