import openai
import os
import json
import httpx
import logging

logger = logging.getLogger(__name__)

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    proxy_url = os.getenv("PROXY_URL")
    
    http_client = None
    if proxy_url:
        http_client = httpx.AsyncClient(proxy=proxy_url)
        
    return openai.AsyncOpenAI(api_key=api_key, http_client=http_client)

async def analyze_linkedin_post(post_text: str, stats: str) -> dict:
    """
    Sends the post text and its statistics to OpenAI to decompose 
    its structure, hooks, and tone of voice.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key missing!")
        return {}

    client = _get_client()

    system_prompt = (
        "Ты — топовый эксперт по продвижению в LinkedIn и копирайтер. "
        "Твоя задача — сделать глубокий 'реверс-инжиниринг' поста пользователя.\n"
        "Пользователь даст тебе текст поста и его статистику (просмотры, лайки).\n"
        "Тебе нужно вернуть JSON-объект со следующей структурой:\n"
        "{\n"
        "  \"hook_analysis\": \"Анализ первого предложения/абзаца (почему он цепляет или нет)\",\n"
        "  \"formatting\": \"Анализ структуры (абзацы, списки, эмодзи)\",\n"
        "  \"tone_of_voice\": \"Характеристика стиля (формальный, дерзкий, сторителлинг)\",\n"
        "  \"call_to_action\": \"Анализ призыва к действию в конце (есть ли он, насколько сильный)\",\n"
        "  \"overall_verdict\": \"Краткий вывод: почему этот пост набрал такую статистику\",\n"
        "  \"reusable_template\": \"Абстрактный шаблон (схема) этого поста, чтобы пользователь мог написать новый пост на другую тему, но точно в такой же структуре\"\n"
        "}\n\n"
        "ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ.\n"
        "ОТВЕЧАЙ СТРОГО В ФОРМАТЕ JSON, без маркдаун оберток (без ```json)."
    )

    user_prompt = f"Текст поста:\n{post_text}\n\nСтатистика:\n{stats}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # or gpt-4-turbo / gpt-3.5-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        
        result_content = response.choices[0].message.content.strip()
        
        # Clean up if OpenAI somehow included markdown
        if result_content.startswith("```json"):
            result_content = result_content[7:]
        if result_content.endswith("```"):
            result_content = result_content[:-3]
            
        return json.loads(result_content)
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return {"error": str(e)}

async def generate_post_ideas(memory_template: str) -> str:
    """
    Generates 3 engaging post ideas/topics based on the user's successful structure 
    and current AI/n8n meta.
    """
    client = _get_client()
    
    system_prompt = (
        "Ты — креативный продюсер для LinkedIn. Твоя ниша: AI интеграции, n8n, автоматизация бизнеса.\n"
        "Пользователь нажал 'Сгенерировать пост', но пока не придумал тему.\n"
        "Твоя задача — предложить 3 сочные, актуальные ИДЕИ (ТЕМЫ) для нового поста.\n"
        "Учитывай структуру Успешного Шаблона пользователя, чтобы идеи подходили под его формат.\n"
        "Идеи должны быть на РУССКОМ языке. Опиши каждую идею в 1-2 предложениях.\n\n"
        "Формат:\n"
        "<b>1. [Название идеи 1]</b> - [Краткое описание]\n\n"
        "<b>2. [Название идеи 2]</b> - [Краткое описание]\n\n"
        "<b>3. [Название идеи 3]</b> - [Краткое описание]\n"
    )
    
    user_prompt = f"Успешный шаблон пользователя:\n{memory_template}"
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating ideas: {e}")
        return f"Произошла ошибка при генерации тем: {e}"

async def generate_post_from_memory(topic: str, memory_template: str) -> str:
    """
    Generates a new LinkedIn post based on a successful template saved in memory.
    """
    client = _get_client()
    
    system_prompt = (
        "Ты — профессиональный ghostwriter для LinkedIn.\n"
        "Тебе дадут тему для нового поста и 'Успешный Шаблон' (схему), по которой нужно написать текст.\n"
        "Твоя задача — написать 3 РАЗНЫХ ВАРИАНТА поста на новую тему, СТРОГО соблюдая структуру, ритм и стиль из шаблона.\n"
        "ВАЖНО: Сами сгенерированные посты ОБЯЗАТЕЛЬНО должны быть НА АНГЛИЙСКОМ ЯЗЫКЕ.\n"
        "Комментарии/заголовки между опциями можешь оставить на русском или сделать на английском.\n"
        "Для разделения вариантов используй HTML-заголовки, например:\n\n"
        "<b>Option 1 (More formal):</b>\n[текст]\n\n<b>Option 2 (More engaging):</b>\n[текст]\n\n<b>Option 3 (Direct to the point):</b>\n[текст]\n\n"
        "НЕ используй Markdown (никаких ** или *). Для выделения используй строго HTML-теги <b> и <i>."
    )
    
    user_prompt = f"Тема для нового поста:\n{topic}\n\nШаблон успешного поста (используй эту структуру):\n{memory_template}"
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating post: {e}")
        return f"Произошла ошибка при генерации: {e}"

async def summarize_news(raw_news_text: str) -> str:
    client = _get_client()
    
    system_prompt = (
        "Ты — AI-эксперт. Тебе дадут сырые новости про n8n и ИИ в бизнесе от поисковика.\n"
        "Сделай из них красивый утренний дайджест для Telegram на русском языке (2-3 самые сочные новости).\n"
        "ОБЯЗАТЕЛЬНО используй HTML-теги для форматирования: <b>жирный</b>, <i>курсив</i>, <u>подчеркнутый</u>, <a>ссылка</a>.\n"
        "НЕ используй Markdown (никаких ** или *), так как это сломает парсер Telegram!"
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_news_text}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error summarizing news: {e}")
        return "Ошибка при суммаризации новостей."
