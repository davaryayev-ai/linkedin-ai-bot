from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db.database import SessionLocal
from db.models import UserMemory
from services.openai_service import generate_post_from_memory, generate_post_ideas
from services.news_service import fetch_n8n_ai_news
import json

router = Router()

@router.message(F.text == "📰 Новости n8n & AI")
@router.message(Command("news"))
async def get_news_now(message: types.Message):
    await message.answer("🔄 Ищу самые свежие новости по n8n и AI интеграциям...")
    news_text = await fetch_n8n_ai_news()
    await message.answer(news_text, parse_mode="HTML")

@router.message(F.text == "✍️ Сгенерировать пост")
async def start_generation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = SessionLocal()
    user_memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    db.close()
    
    if not user_memory or not user_memory.successful_structures:
        await message.answer("У тебя пока нет сохраненных шаблонов в 'Памяти'.\nСначала проанализируй хотя бы один свой успешный пост! (Кнопка 'Анализ поста')")
        return
        
    await state.update_data(memory=user_memory.successful_structures)
    
    # Generate ideas based on the latest template
    templates = json.loads(user_memory.successful_structures)
    selected_template = templates[-1]
    
    await message.answer("🔄 Анализирую твой успешный шаблон и генерирую **Идеи для постов**...", parse_mode="Markdown")
    
    ideas = await generate_post_ideas(selected_template)
    
    await message.answer(
        f"💡 <b>Вот 3 актуальные идеи для твоего нового поста:</b>\n\n"
        f"{ideas}\n\n"
        "Напиши мне <b>выбранную тему</b> (или предложи свою), и я напишу по ней готовый пост на английском:", 
        parse_mode="HTML"
    )
    await state.set_state("waiting_for_generation_topic")

@router.message(F.state == "waiting_for_generation_topic")
async def process_generation_topic(message: types.Message, state: FSMContext):
    topic = message.text
    data = await state.get_data()
    memory_json = data.get("memory")
    
    # Just take the first template for simplicity, or we can make user choose
    templates = json.loads(memory_json)
    selected_template = templates[-1] # simplest: take the most recently added template
    
    await message.answer("✍️ Генерирую пост по твоему успешному шаблону... ⏳")
    
    generated_text = await generate_post_from_memory(topic, selected_template)
    
    await message.answer(f"<b>Твои варианты постов (на английском):</b>\n\n{generated_text}\n\n<i>Выбирай лучший, копируй и публикуй!</i>", parse_mode="HTML")
    await state.clear()
