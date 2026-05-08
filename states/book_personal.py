from aiogram.fsm.state import State, StatesGroup


class BookPersonalQuiz(StatesGroup):
    answering = State()
    describing = State()
