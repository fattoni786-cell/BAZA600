from aiogram.fsm.state import State, StatesGroup


class MoviePersonalQuiz(StatesGroup):
    answering = State()
    describing = State()
