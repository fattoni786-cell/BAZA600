from aiogram.fsm.state import State, StatesGroup


class PremiumPromoFlow(StatesGroup):
    waiting_code = State()
