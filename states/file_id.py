from aiogram.fsm.state import State, StatesGroup


class FileIdTool(StatesGroup):
    waiting_media = State()
