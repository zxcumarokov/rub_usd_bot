import os
import requests
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, executor, types  # mid
from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


# TOKEN = "5991863328:AAHf0Fyz3rtMR8851RF3xfyqdzIYNNDbVnM"
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("You have forgot to set TOKEN environment variable")

# cb = CallbackData("ikb", "action")  # cb filter
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Глобальная переменная для хранения текущего курса


class Form(StatesGroup):
    waiting_for_usd = State()
    waiting_for_rub = State()


def is_float(string: str) -> bool:
    string = string.replace(",", ".")
    try:
        float(string)
        return True
    except ValueError:
        return False


# Функция для обновления данных о курсе
async def update_exchange_rate() -> float | None:
    url = "https://www.google.com/finance/quote/USD-RUB?sa=X&ved=2ahUKEwjoxe30pcCBAxW3AhAIHfMmAxYQmY0JegQIDRAr"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"  # noqa E501
    }
    full_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(full_page.content, "html.parser")
    convert = soup.findAll("div", {"class": "YMlKec fxKbKc"})

    if convert:
        return float(convert[0].text.replace(",", "."))
    else:
        return None


# Функция для создания клавиатуры
def get_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Доллары в рубли", callback_data="usd_to_rub"))
    keyboard.add(InlineKeyboardButton("Рубли в доллары", callback_data="rub_to_usd"))

    return keyboard


# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Выберите операцию:", reply_markup=get_keyboard())


# Обработчик нажатия на кнопку "Доллары в рубли"
@dp.callback_query_handler(lambda c: (c.data == "usd_to_rub"))
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await Form.waiting_for_usd.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите количество долларов для конвертации:"
    )


# Обработчик нажатия на кнопку "Рубли в доллары"
@dp.callback_query_handler(lambda c: (c.data == "rub_to_usd"))
async def process_callback_button2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await Form.waiting_for_rub.set()
    await bot.send_message(
        callback_query.from_user.id,
        "Введите количество рублей для конвертации в доллары:",
    )


# Обработчик ввода количества рублей
@dp.message_handler(lambda message: is_float(message.text), state=Form.waiting_for_rub)
async def process_rub_amount(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    rub_amount = float(message.text.replace(",", "."))
    rate = await update_exchange_rate()
    if not rate:
        await message.answer("Не удалось получить курс обмена")
        return
    usd = rub_amount / rate
    await bot.send_message(user_id, f"{rub_amount} рублей равно {usd} долларов")


# Обработчик ввода количества долларов
@dp.message_handler(lambda message: is_float(message.text), state=Form.waiting_for_usd)
async def process_usd_amount(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    usd_amount = float(message.text.replace(",", "."))
    rate = await update_exchange_rate()
    if not rate:
        await message.answer("Не удалось получить курс обмена")
        return
    rub = usd_amount * rate
    await bot.send_message(user_id, f"{usd_amount} долларов равно {rub} рублей")


# Основная функция
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
