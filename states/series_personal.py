from aiogram.fsm.state import State, StatesGroup


class SeriesPersonalQuiz(StatesGroup):
    answering = State()
    describing = State()
