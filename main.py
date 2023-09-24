
import requests
from bs4 import BeautifulSoup
import time
import hashlib  # берет сторку и возвращает закодированую строку используе для id
from aiogram import Bot, Dispatcher, executor, types, Bot  # mid
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup  # keyboards
from aiogram.utils.callback_data import CallbackData  # cb filter
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent  # inline mod
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery

TOKEN = '5991863328:AAHf0Fyz3rtMR8851RF3xfyqdzIYNNDbVnM'
cb = CallbackData('ikb', 'action')  # cb filter
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)




USD_RUB = 'https://www.google.com/finance/quote/USD-RUB?sa=X&ved=2ahUKEwjoxe30pcCBAxW3AhAIHfMmAxYQmY0JegQIDRAr'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}





amount = 1  #float(input())

# Глобальная переменная для хранения текущего курса
current_usd_to_rub = None
usd_or_rub = None






# Функция для обновления данных о курсе
def update_exchange_rate():
    global current_usd_to_rub

    full_page = requests.get(USD_RUB, headers=headers)
    soup = BeautifulSoup(full_page.content, 'html.parser')
    convert = soup.findAll("div", {"class": "YMlKec fxKbKc"})

    if convert:
        usdtorub = convert[0].text
        usdtorub2 = usdtorub.replace(',', '.')
        usdtorub2 = float(usdtorub2)
        current_usd_to_rub = usdtorub2


# Функция для создания клавиатуры
def get_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Доллары в рубли", callback_data='usd_to_rub'))
    keyboard.add(InlineKeyboardButton("Рубли в доллары", callback_data='rub_to_usd'))
    return keyboard

def get_keybord() -> InlineKeyboardMarkup: #создаем клавы в сообщении которые при нажатии создают каллбекдату
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                'русский',
                callback_data = 'данные при нажатии кнопки'
            ),
            InlineKeyboardButton(
                'английский',
                callback_data='данные при нажатии кнопки'
            ),
                InlineKeyboardButton(
                    'казахский',
                    callback_data='данные при нажатии кнопки'
                )],
        ]
    )
    return ikb
# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Выберите операцию:", reply_markup=get_keyboard())

# Обработчик нажатия на кнопку
@dp.callback_query_handler(lambda callback_query: True)
async def button_click(callback_query: CallbackQuery):
    global usd_or_rub
    if callback_query.data == 'usd_to_rub':
        usd_or_rub = 1
        await bot.send_message(callback_query.from_user.id, "Введите количество долларов для конвертации:")
    elif callback_query.data == 'rub_to_usd':
        usd_or_rub = 2
        await bot.send_message(callback_query.from_user.id, "Введите количество рублей для конвертации в доллары:")


# Обработчик ввода количества долларов
@dp.message_handler(lambda message: message.text.isdigit(), state='*')
async def process_usd_amount(message: types.Message):
    usd_amount = int(message.text)
    await convert_and_send_result(message.from_user.id, usd_amount)

# Функция для конвертации и отправки результата
async def convert_and_send_result(user_id, usd_amount):
    global current_usd_to_rub
    global usd_or_rub

    if usd_or_rub == 1:
        rub_amount = usd_amount * current_usd_to_rub
        rub_amount_rounded = round(rub_amount, 2)  # Округляем до двух знаков после запятой
        await bot.send_message(user_id, f"{usd_amount} долларов равно {rub_amount_rounded} рублей")

    else:
        rub_amount = usd_amount / current_usd_to_rub
        rub_amount_rounded = round(rub_amount, 2)  # Округляем до двух знаков после запятой
        await bot.send_message(user_id, f"{usd_amount} рублей равно {rub_amount_rounded} долларов")



# функция выбора яязыка
@dp.message_handler(commands=['language'])
async def cmd_start(message: types.Message) -> None:
    await message.answer(f'выбирите язык ',
                         reply_markup=get_keybord())
# Основная функция
if __name__ == '__main__':
    update_exchange_rate()  # Обновляем данные о курсе при запуске
    executor.start_polling(dp, skip_updates=True)

