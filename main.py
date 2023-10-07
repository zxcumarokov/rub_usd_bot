import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from config import TOKEN
from models import Language, Phrase

from db_engine import engine

# cb = CallbackData("ikb", "action")  # cb filter
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Класс для хранения состояний
class Form(StatesGroup):
    waiting_for_usd = State()
    waiting_for_rub = State()


def is_float(string: str) -> bool:  # noqa E501
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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
        # noqa E501
    }
    full_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(full_page.content, "html.parser")
    convert = soup.findAll("div", {"class": "YMlKec fxKbKc"})

    if convert:
        return float(convert[0].text.replace(",", "."))
    else:
        return None


# Функция для создания клавиатуры
def get_direction_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Доллары в рубли", callback_data="usd_to_rub"))
    keyboard.add(InlineKeyboardButton("Рубли в доллары", callback_data="rub_to_usd"))

    return keyboard


# Функция для создания клавиатуры на нужном языке
def get_languages_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    with Session(engine) as session:
        languages = session.scalars(select(Language)).all()
        for language in languages:
            keyboard.add(
                InlineKeyboardButton(
                    text=language.name,
                    callback_data=f"set_language_{language.name}",
                )
            )
    return keyboard


# Измененный обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    # Проверяем наличие пользователя в базе данных
    with Session(engine) as session:
        user = session.scalars(
            select(User)
            .where(User.id == user_id)
        ).one_or_none()
        
        if user is not None:
            message_text = session.scalars(
                select(Phrase)
                .where(Phrase.language_id == user.language_id)
                .where(Phrase.phrase_code == "start")
            ).one_or_none()
            await message.answer(
                text=,
                reply_markup=get_keyboard2(existing_user.language),
            )
        else:
            # Пользователь отсутствует в базе, предложить выбор языка
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="set_language_ru"))
            markup.add(InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en"))
            await message.answer("Выберите язык:", reply_markup=markup)


# Обработчик нажатия на кнопку выбора языка
@dp.callback_query_handler(lambda c: c.data in ["set_language_ru", "set_language_en"])
async def set_user_language(callback_query: types.CallbackQuery):
    global language  # Объявляем, что будем использовать глобальную переменную
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    selected_language = callback_query.data.replace("set_language_", "")

    # Создаем запись в таблице languages

    new_language = Language(user_id=user_id, language=selected_language)
    session.add(new_language)
    session.commit()

    # После выбора языка, предложите выбрать операцию
    await bot.send_message(
        user_id,
        get_operation_message(selected_language),
        reply_markup=get_keyboard2(selected_language),
    )


# Обработчик команды /language
@dp.message_handler(commands=["language"])
async def set_language(message: types.Message):
    global language  # Объявляем, что будем использовать глобальную переменную
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="set_language_ru"))
    markup.add(InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en"))

    await message.answer("Выберите язык:", reply_markup=markup)


def get_user_language(user_id):
    user_language = session.query(Language).filter_by(user_id=user_id).first()
    return (
        user_language.language if user_language else "en"
    )  # Вернуть английский язык по умолчанию, если язык не
    # найден


# Обработчик нажатия на кнопку "Доллары в рубли"
@dp.callback_query_handler(lambda c: (c.data == "usd_to_rub"))
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await Form.waiting_for_usd.set()
    user_id = callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    if language == "ru":
        await bot.send_message(user_id, f"Введите количество долларов для конвертации:")
    elif language == "en":
        await bot.send_message(user_id, f"Enter the amount of dollars to convert:")


@dp.callback_query_handler(lambda c: c.data in ["set_language_ru", "set_language_en"])
async def set_user_language(callback_query: types.CallbackQuery, session=None):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    selected_language = callback_query.data.replace("set_language_", "")

    # Создаем запись в таблице languages
    new_language = Language(user_id=user_id, language=selected_language)
    session.add(new_language)
    session.commit()

    await bot.send_message(user_id, f"Вы выбрали язык: {selected_language}")


# обработчик нажатия на кнопку "рубли в доллары" с ответом в зависимости от выбраного языка
@dp.callback_query_handler(lambda c: (c.data == "rub_to_usd"))
async def process_callback_button2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await Form.waiting_for_rub.set()
    user_id = callback_query.from_user.id
    language = get_user_language(user_id)
    if language == "ru":
        await bot.send_message(
            user_id, f"Введите количество рублей для конвертации в доллары:"
        )
    elif language == "en":
        await bot.send_message(
            user_id, f"Enter the amount of rubles to convert to dollars:"
        )


# Обработчик ввода количества рублей
@dp.message_handler(lambda message: is_float(message.text), state=Form.waiting_for_rub)
async def process_rub_amount(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    language = get_user_language(user_id)

    rub_amount = float(message.text.replace(",", "."))
    rate = await update_exchange_rate()
    if not rate:
        await message.answer("Не удалось получить курс обмена")
        return

    usd = rub_amount / rate
    usd = round(usd, 2)

    if language == "ru":
        await bot.send_message(user_id, f"{rub_amount} рублей равно {usd} долларов")
    elif language == "en":
        await bot.send_message(
            user_id, f"{rub_amount} rubles is equal to {usd} dollars"
        )


# Обработчик ввода количества долларов
@dp.message_handler(lambda message: is_float(message.text), state=Form.waiting_for_usd)
async def process_usd_amount(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    language = get_user_language(user_id)

    usd_amount = float(message.text.replace(",", "."))
    rate = await update_exchange_rate()
    if not rate:
        await message.answer("Не удалось получить курс обмена")
        return

    rub = usd_amount * rate
    rub = round(rub, 2)

    if language == "ru":
        await bot.send_message(user_id, f"{usd_amount} долларов равно {rub} рублей")
    elif language == "en":
        await bot.send_message(
            user_id, f"{usd_amount} dollars is equal to {rub} rubles"
        )


################DB##################### # noqa E501

# Base = declarative_base()


# Создаем соединение с БД

# Создаем таблицу
# Base.metadata.create_all(engine)

# Создаем сессию для работы с БД
# Session = sessionmaker(bind=engine)
# session = Session()


def delete_all_data(session):
    try:
        # Удаляем все данные из таблицы Language
        delete_statement = delete(Language)
        session.execute(delete_statement)
        session.commit()
        print("Все данные удалены из таблицы Language.")
    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении данных: {str(e)}")
    finally:
        session.close()


# Используйте эту функцию для удаления данных из базы данных
# delete_all_data(session)
# Пример запроса данных из таблицы languages
languages = session.query(Language).all()
for language in languages:
    print(f"User ID: {language.user_id}, Language: {language.language}")

# Не забудь закрыть сессию при завершении работы
session.close()

# Основная функция
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
