from aiogram.fsm.state import State, StatesGroup


class AnimePersonalQuiz(StatesGroup):
    answering = State()
    describing = State()
