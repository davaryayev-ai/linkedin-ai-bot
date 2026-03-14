from aiogram.fsm.state import StatesGroup, State

class AnalyzePost(StatesGroup):
    waiting_for_text = State()
    waiting_for_stats = State()
    waiting_for_image = State()
