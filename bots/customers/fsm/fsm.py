from aiogram.fsm.state import State, StatesGroup


class CustomerState(StatesGroup):
    unauthorized = State()
    authorized = State()
    waiting_for_location = State()
    waiting_for_file = State()