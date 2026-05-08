from aiogram.fsm.state import State, StatesGroup


class CommunitySuggestionFlow(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_vibe = State()
