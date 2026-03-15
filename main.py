import asyncio
import logging
import os
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers import commands, posts, features
from db.database import init_db
from services.news_service import fetch_n8n_ai_news

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN is not set in .env")
        return

    # Initialize Database
    init_db()

    # Setup Proxy for PythonAnywhere if needed
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        logger.info(f"Using proxy: {proxy_url}")
        session = AiohttpSession(proxy=proxy_url)
        bot = Bot(token=bot_token, session=session)
    else:
        bot = Bot(token=bot_token)
        
    dp = Dispatcher()
    
    # Register routers (handlers)
    dp.include_router(commands.router)
    dp.include_router(posts.router)
    dp.include_router(features.router)

    # Initialize Scheduler
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    async def scheduled_news():
        admin_id = os.getenv("ADMIN_ID")
        if not admin_id:
            logger.warning("ADMIN_ID not set, cannot send scheduled news.")
            return
        logger.info("Fetching scheduled daily news...")
        news = await fetch_n8n_ai_news()
        try:
            await bot.send_message(chat_id=admin_id, text=f"🌅 Утренний дайджест AI & n8n:\n\n{news}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send scheduled news: {e}")

    # Add job every day at 10:00 AM (Moscow time)
    scheduler.add_job(scheduled_news, 'cron', hour=10, minute=0)
    scheduler.start()

    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
