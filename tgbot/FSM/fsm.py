from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    unauthorized = State()
    authorized = State()
    waiting_for_location = State()
    waiting_for_photo = State()
