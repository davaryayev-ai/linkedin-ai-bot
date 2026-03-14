import asyncio
from duckduckgo_search import DDGS
from services.openai_service import summarize_news
import logging

logger = logging.getLogger(__name__)

async def fetch_n8n_ai_news() -> str:
    """
    Fetches latest news regarding n8n, AI business applications, and automation.
    Summarizes them using OpenAI.
    """
    try:
        results = []
        with DDGS() as ddgs:
            # Search for n8n AI news in the past day/week
            ddg_results = ddgs.news("n8n AI automation business", max_results=5)
            for r in ddg_results:
                results.append(f"Заголовок: {r.get('title')}\nИсточник: {r.get('source')}\nОписание: {r.get('body')}\nСсылка: {r.get('url')}\n")
        
        if not results:
            return "Свежих новостей по n8n и AI интеграциям за сегодня не найдено."

        raw_news_text = "\n".join(results)
        
        # Summarize with OpenAI
        summary = await summarize_news(raw_news_text)
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return "Произошла ошибка при поиске новостей."
