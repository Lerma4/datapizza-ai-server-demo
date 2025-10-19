from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient
from datapizza.tools.duckduckgo import DuckDuckGoSearchTool
from app.config import get_openai_api_key
from app.agent.tools.weather_tools import get_weather
from app.agent.tools.search_tools import web_search

client = OpenAIClient(api_key=get_openai_api_key(), model="gpt-4o-mini")

# System prompt per l'agente incident/viabilità
INCIDENT_SYSTEM_PROMPT = (
    """
    You are an expert agent focused on road mobility and incidents. Your job is to identify and summarize
    recent, reliable news and online information that can disrupt circulation or transport, including:
    - Strikes, protests, demonstrations, road closures, construction works, accidents, slowdowns,
      and public transport service disruptions.
    - Traffic problems: queues, blockages, restrictions, detours, and limitations.
    - Adverse weather conditions: heavy rain, hail, strong winds, ice, snow, and official weather alerts.

    Input:
    - The prompt will include a date in standard computer date format (ISO 8601, e.g., YYYY-MM-DD). Use this date to scope searches and forecasts to that day and any relevant surrounding window.

    Instructions:
    - Always include date/time, location, and severity of impact; cite sources.
    - Highlight practical impacts on mobility/traffic, with concise operational recommendations.
    - Use available tools for weather and web search when necessary.
    - Provide a short summary and links to main sources.
    """
)

def run_incident_agent(prompt: str) -> str:
    
    weather_agent = Agent(
        name="weather_agent", 
        tools=[get_weather],
        system_prompt="You are a weather expert. Provide detailed weather information and forecasts. Dates passed to this tool must be in the format 'YYYY-MM-DD'.",
        client=client
    )
    
    web_search_agent = Agent(
        name="web_search_expert",
        client=client,
        system_prompt="You are a web search expert. You can search the web for information.",
        tools=[DuckDuckGoSearchTool()]
    )
    
    incident_agent = Agent(
        name="incident_agent",
        system_prompt=INCIDENT_SYSTEM_PROMPT,
        client=client
    )
    
    incident_agent.can_call([weather_agent, web_search_agent])
    
    response = incident_agent.run(prompt)
    return response.text

if __name__ == "__main__":
    print(run_incident_agent("What's the weather on 2024-09-20 in Milan?"))
    # Output:
    # Tomorrow in Milan, the temperature will be 25 °C.