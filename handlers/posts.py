from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from .states import AnalyzePost
from db.database import SessionLocal
from db.models import AnalyzedPost, UserMemory
from services.openai_service import analyze_linkedin_post
import logging
import json

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "📊 Анализ поста")
@router.message(Command("analyze"))
async def start_analysis(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Давай проанализируем твой пост! 🚀\n\n"
        "Для начала, отправь мне <b>текст поста</b> (можно скопировать из LinkedIn).",
        parse_mode="HTML"
    )
    await state.set_state(AnalyzePost.waiting_for_text)

@router.message(AnalyzePost.waiting_for_text, F.text)
async def process_text(message: types.Message, state: FSMContext):
    await state.update_data(post_text=message.text)
    
    await message.answer(
        "Текст получен! ✅\n\n"
        "Теперь напиши статистику поста через пробел или запятую.\n\n"
        "👉 Например: <b>2413 просмотров, 50 лайков, 10 комментариев</b>\n"
        "👉 Или просто цифры: <b>2413 50 10</b>",
        parse_mode="HTML"
    )
    await state.set_state(AnalyzePost.waiting_for_stats)

@router.message(AnalyzePost.waiting_for_stats, F.text)
async def process_stats(message: types.Message, state: FSMContext):
    # Parse stats simply for now
    stats_text = message.text
    # We will refine parsing later, for now just store the string or parse basic ints
    
    await state.update_data(stats_raw=stats_text)
    
    await message.answer(
        "Статистика сохранена! 📊\n\n"
        "Если в посте была <b>картинка</b>, отправь её сейчас.\n"
        "Если картинки не было, просто нажми /skip_image",
        parse_mode="HTML"
    )
    await state.set_state(AnalyzePost.waiting_for_image)

@router.message(AnalyzePost.waiting_for_image, F.photo)
async def process_image(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await finish_analysis(message, state)

@router.message(AnalyzePost.waiting_for_image, Command("skip_image"))
async def skip_image(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await finish_analysis(message, state)

async def finish_analysis(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_text = data.get("post_text")
    stats_raw = data.get("stats_raw")
    
    # Notify user
    await message.answer(
        "✅ Все данные собраны! Начинаю глубокий анализ с помощью ИИ...\n"
        "Это займет буквально секунд 10-15 ⏳"
    )
    
    # Call OpenAI
    analysis_result = await analyze_linkedin_post(post_text, stats_raw)
    
    if "error" in analysis_result:
        await message.answer("❌ Возникла ошибка при обращении к OpenAI. Проверь API ключ в .env.")
        await state.clear()
        return

    # Extract info
    hook = analysis_result.get("hook_analysis", "Нет данных").replace("**", "")
    verdict = analysis_result.get("overall_verdict", "Нет данных").replace("**", "")
    formatting = analysis_result.get("formatting", "Нет данных").replace("**", "")
    template = analysis_result.get("reusable_template", "Нет данных")
    
    # Save to Database
    db = SessionLocal()
    try:
        user_id = message.from_user.id
        # 1. Save the Analyzed Post
        new_post = AnalyzedPost(
            user_id=user_id,
            post_text=post_text,
            analysis_result=analysis_result
        )
        db.add(new_post)
        
        # 2. Update User Memory (upsert logic)
        user_memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
        if not user_memory:
            user_memory = UserMemory(user_id=user_id, successful_structures=json.dumps([template]))
            db.add(user_memory)
        else:
            # Append new template to memory
            existing_templates = []
            if user_memory.successful_structures:
                try:
                    existing_templates = json.loads(user_memory.successful_structures)
                except:
                    pass
            existing_templates.append(template)
            user_memory.successful_structures = json.dumps(existing_templates)
            
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

    # Send result to user
    report = (
        "🧠 <b>Анализ завершен!</b>\n\n"
        f"🎯 <b>Хук (Как цепляет):</b>\n{hook}\n\n"
        f"📝 <b>Форматирование:</b>\n{formatting}\n\n"
        f"⚖️ <b>Вердикт:</b>\n{verdict}\n\n"
        "〰️〰️〰️〰️〰️〰️〰️\n"
        "💾 <i>Шаблон этого поста бережно сохранен в твою Память.</i>\n"
        "👉 Теперь ты можешь сгенерировать классный новый пост по этой структуре через меню!"
    )
    
    await message.answer(report, parse_mode="HTML")
    
    # Clear state
    await state.clear()

@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действие отменено. ❌")
