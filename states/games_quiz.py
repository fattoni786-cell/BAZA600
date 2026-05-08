from aiogram.fsm.state import StatesGroup, State


class GameQuiz(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
