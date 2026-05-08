from aiogram.fsm.state import State, StatesGroup


class GamePersonalQuiz(StatesGroup):
    answering = State()
    describing = State()
