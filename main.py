import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaPhoto, ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "6530825419:AAGKU7Fy4w18uzgFzFJ0RVYdMHWQYuDPLLQ"
CHAT_ID = -1002131377903
CHAT_ID_meat = 114
CHAT_ID_MILK_KMK = 113
CHAT_ID_MILK_AGATA = 112 #

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class Form(StatesGroup):
    Start = State()
    Photos = State()
    Date = State()
    InvoiceNumber = State()
    Supplier = State()
    Location = State()
    Theme = State()
    Amount = State()
    Confirm = State()


keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(types.KeyboardButton("Прислать накладную"))


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply(
        f"Привет! {message.from_user.first_name} Этот бот поможет вам отправить информацию в другой чат.",
        reply_markup=keyboard,
    )
    await message.reply(
        text="Для начала воспользуйтесь кнопкой \n'Прислать накладную' \nили \n/next_document",
        reply_markup=keyboard,
    )


@dp.message_handler(commands=["next_document"], state="*")
async def send_invoice(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply(
        "Хорошо! Теперь пришлите фотографии накладной (1/2/3), по одной."
    )
    await Form.Photos.set()


@dp.message_handler(commands=["."])
async def send(message: types.Message):
    msg = message.message_id
    info = message.from_user.id
    print(msg,info)


@dp.message_handler(
    lambda message: message.text.lower() == "прислать накладную", state="*"
)
async def send_invoice(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply(
        "Хорошо! Теперь пришлите фотографии накладной (1/2/3), по одной."
    )
    await Form.Photos.set()


@dp.message_handler(commands=["skip"], state=Form.Photos)
async def skip_photos(message: types.Message):
    await message.reply(
        "Вы решили пропустить отправку фотографий. Теперь введите дату в формате 13/04/2022:"
    )
    await Form.next()


@dp.message_handler(content_types=["photo"], state=Form.Photos)
async def process_photos(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "photos" not in data:
            data["photos"] = []

        data["photos"].append(message.photo[-1].file_id)

        if len(data["photos"]) < 3:
            await message.reply(
                f"Фотография {len(data['photos'])} принята. Пришлите еще фотографию "
                f"Вы также можете воспользоваться командой /skip для пропуска этого шага:"
            )
        else:
            await message.reply(
                "Все фотографии приняты. Теперь введите дату в формате 13/04/2022:"
            )
            await Form.next()


@dp.message_handler(state=Form.Date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["date"] = message.text

    await Form.next()
    await message.reply("Введите номер накладной:")


@dp.message_handler(state=Form.InvoiceNumber)
async def process_invoice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["invoice_number"] = message.text

    await Form.next()
    await message.reply("Введите поставщика:")


@dp.message_handler(state=Form.Supplier)
async def process_supplier(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["supplier"] = message.text

    await Form.next()
    await message.reply("Введите точку:")


@dp.message_handler(state=Form.Location)
async def process_location(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["location"] = message.text

    await Form.next()
    await message.reply("Введите сумму:")


@dp.message_handler(state=Form.Theme)
async def process_location(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["amount"] = message.text
    themes = ["Молочная Продукция КМК", "Молочная продукция Агат", "Фарш/Сосиски"]

    # Отправляем предварительно заготовленные темы для выбора
    keyboard_theme = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for theme in themes:
        keyboard_theme.add(types.KeyboardButton(theme))

    await Form.next()
    await message.reply("Выберите тему:", reply_markup=keyboard_theme)


@dp.message_handler(state=Form.Amount)
async def confirm_information(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["theme"] = message.text
        theme = data["theme"]

        # Определяем chat_id в зависимости от выбранной темы
        if theme == "Фарш/Сосиски":
            chat_id_theme = CHAT_ID_meat
        elif theme == "Молочная Продукция КМК":
            chat_id_theme = CHAT_ID_MILK_KMK
        elif theme == "Молочная продукция Агат":
            chat_id_theme = CHAT_ID_MILK_AGATA

        info_message = (
            f"Дата: {data['date']}\nНомер накладной: {data['invoice_number']}\n"
            f"Поставщик: {data['supplier']}\nТочка: {data['location']}\nСумма: {data['amount']}\n"
            f"Тема: {data['theme']}\n"
        )

        media = [InputMediaPhoto(media_id) for media_id in data["photos"]]
        await bot.send_media_group(
            chat_id=CHAT_ID, media=media,reply_to_message_id=chat_id_theme,
        )
        await bot.send_message(
            chat_id=CHAT_ID, text=info_message,
            parse_mode=ParseMode.MARKDOWN,reply_to_message_id=chat_id_theme,

        )

        await message.reply("Информация и фотографии отправлены в другой чат.")
        await state.finish()  # Сброс состояния и данных
        await message.reply(
            text="Что бы прислать еще наклданую воспользуйтесь кнопкой \n 'Прислать накладную' \nили \n/next_document",
            reply_markup=keyboard,

        )


if __name__ == "__main__":
    from aiogram import executor

    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
