import asyncio
import datetime
import sqlite3
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from config_bot import token_bot
from database import parsing_domins
from aiogram.utils.exceptions import BotBlocked


bot = Bot(token=token_bot, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
conn = sqlite3.connect('Posts.db')
cur = conn.cursor()
can = sqlite3.connect('Users.db')
curs = can.cursor()

BUT_AND_HASH = {"buttonTC": "#TechnoCom", "buttonITF": "#ITfest_2022",
                "buttonIASF": "#IASF2022", "buttonOKK": "#okk_fest",
                "buttonNF": "#Нейрофест", "buttonINVIW": "#НевидимыйМир",
                "buttonNIR": "#КонкурсНИР", "buttonVRAR": "#VRARFest3D"}

BUT_AND_DOMAINS = {"butnewsTC": "#TechnoCom", "butnewsITF": "#ITfest_2022",
                   "butnewsIASF": "#IASF2022", "butnewsOKK": "#ФестивальОКК",
                   "butnewsNF": "#Нейрофест", "butnewsINVIW": "#НевидимыйМир",
                   "butnewsNIR": "#КонкурсНИР", "butnewsVRAR": "#VRARFest3D"}

HASH_UNSUB = {"#TechnoCom": "/unsub_TechnoCom", "#ITfest_2022": "/unsub_ITfest_2022",
              "#IASF2022": "/unsub_IASF2022", "#okk_fest": "/unsub_okk_fest",
              "#Нейрофест": "/unsub_Neurofest", "#НевидимыйМир": "/unsub_Invisible_World",
              "#КонкурсНИР": "/unsub_competitionNIR", "#VRARFest3D": "/unsub_VRARFest3D"}


@dp.message_handler(commands="help")
async def help_user(message: types.Message):
    await message.answer("""<b>Это справочник по командам бота.</b>
Перезапуск бота, нажми /start  
Вывод контактов организатора, нажми /contacts
Вывод подписок на мероприятия, нажми /mysubs
Для подписки на мероприятия и вывода 3 новостей нажми:
/TechnoCom
/ITfest_2022
/IASF2022
/okk_fest
/Neurofest
/Invisible_World
/competitionNIR
/VRARFest3D
Отписаться от всех новостей мероприятия
/all_unsub
Отписаться от новостей любого мероприятия:
/unsub_TechnoCom
/unsub_ITfest_2022
/unsub_IASF2022
/unsub_okk_fest
/unsub_Neurofest
/unsub_Invisible_World
/unsub_competitionNIR
/unsub_VRARFest3D""")


@dp.message_handler(commands="contacts")
@dp.message_handler(Text(equals="Контакты"))
async def contacts(message: types.Message):
    await message.answer("""Привет! Если у вас возникли какие-либо вопросы, то вот наши контакты:
<b>Группа ВКонтакте</b>
https://vk.com/nauchim.online
<b>Сайт с мероприятиями</b>
https://www.научим.online""")


@dp.message_handler(commands="mysubs")
@dp.message_handler(Text(equals="Мои подписки"))
async def my_subscriptions(message: types.Message):
    """
    Данная функция используется для вывода подписок пользователя
    """
    id_player = message.from_user.id
    check_save = can.execute("""SELECT * FROM users WHERE iduser = ? """,
                             (int(id_player),)).fetchone()
    # достаем информацию по пользователю из базы данных
    if isinstance(check_save, tuple):
        subs = '\n'.join([str(i) for i in check_save[1].split()])
        un_command = '\n'.join([HASH_UNSUB[i] for i in [str(i) for i in check_save[1].split()]])
        # un_command - ссылки-команды для отписки от определенной рассылки
        await message.answer(f"""<b>Твои мероприятия:</b>
<b>{subs}</b>

Отписаться от рассылки новостей сообщества, нажми на хэштэг:
<b>{un_command}</b>
Отписаться от всех новостей
 <b>/all_unsub</b>""")
    else:
        await message.answer('<b>Вы не подписаны ни на одно сообщество</b>')


@dp.message_handler(commands="all_unsub")
async def all_unsub(message: types.Message):
    """
    Данная функция используется для отписки от всех рассылок пользователя
    """
    id_player = message.from_user.id
    check_save = can.execute("""SELECT * FROM users WHERE iduser = ? """,
                             (int(id_player),)).fetchone()
    # достаем информацию по пользователю из базы данных
    if isinstance(check_save, tuple):
        delete = """Delete from users where iduser = ?"""
        can.execute(delete, (id_player,))
        can.commit()
        # удаляем всю информацию о пользователе из базы
        await message.answer('Вы отписались от всех рассылок')
    else:
        await message.answer('<b>Вы не подписаны ни на одно сообщество</b>')


@dp.message_handler(commands=["unsub_TechnoCom", "unsub_ITfest_2022", "unsub_IASF2022",
                              "unsub_okk_fest", "unsub_Neurofest",
                              "unsub_Invisible_World", "unsub_competitionNIR", "unsub_VRARFest3D"])
async def unsub_on_hash(message: types.Message):
    """
    Данная функция используется для отписки от определенной рассылки
    """
    id_player = message.from_user.id
    check_save = can.execute("""SELECT * FROM users WHERE iduser = ? """,
                             (int(id_player),)).fetchone()
    if isinstance(check_save, tuple):
        sub = [str(i) for i in check_save[1].split()]
        # подписки пользователя
        hash_sub = [i for i, v in HASH_UNSUB.items() if v == message.text][0]
        if hash_sub in sub:
            sub.remove(hash_sub)
            if not bool(sub):
                delete = """Delete from users where iduser = ?"""
                can.execute(delete, (id_player,))
                # полное удаление пользователя, если он отписался от единственной рассылки
            else:
                update = """Update users set subscibes = ? where iduser = {}""".format(id_player)
                can.execute(update, (str(" ".join(sub)),))
                # изменение подписок пользователя
            can.commit()
            await message.answer(f'Вы отписались от рассылки по {hash_sub}')
        else:
            await message.answer('Вы не подписаны на данную рассылку')
    else:
        await message.answer('<b>Вы не подписаны ни на одно сообщество</b>')


@dp.message_handler(Text(equals="Последние 10 новостей"))
async def get_10_news(message: types.Message):
    rec = cur.execute('SELECT time, url, text FROM need_post ORDER BY time DESC').fetchall()[:10]
    for i in rec:
        news = f"<b>{datetime.datetime.fromtimestamp(i[0])}</b>\n" \
               f"{i[2]}\n" \
               f"<u>{i[1]}</u>\n"
        await message.answer(news)
        # отправка 10 новостей по всем хэштэгам  в чат пользователю


@dp.message_handler(Text(equals="Вернуться"))
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    """
    Данная функция используется для приветственной фразы и создания кнопок клавиатуры
    """
    button_1 = types.KeyboardButton(text="Последние 10 новостей")
    button_2 = types.KeyboardButton(text="Подпишись на новости")
    button_mysubs = KeyboardButton('Мои подписки')
    button_contact = KeyboardButton('Контакты')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button_1).add(button_2).\
        add(button_mysubs).add(button_contact)
    await message.answer("""Привет! Это телеграмм бот по хэштэгам!
Для справки и помощи по командам бота, нажми на /help""", reply_markup=keyboard)


@dp.callback_query_handler(text=["butnewsTC", "butnewsITF", "butnewsIASF",
                                 "butnewsOKK", "butnewsNF", "butnewsINVIW",
                                 "butnewsNIR", "butnewsVRAR"])
async def send_news(call: types.CallbackQuery):
    """
    Данная функция используется для вывода 3 новостей по определенному хэштэгу
    """
    news = []
    received_button = call.data
    updates = conn.execute("SELECT hashstags, time, url,"
                           " text FROM need_post ORDER BY time DESC").fetchall()
    # запрос новостей из базы данных
    hash_sub = BUT_AND_DOMAINS[received_button]
    for update in updates:
        if hash_sub in update[0].split():
            news.append(update)
        if len(news) == 3:
            break
        # подбор  последних 3 новостей по запрошенному хэштэгу"
    if bool(news):
        for i in news:
            new_send = f"<b>{datetime.datetime.fromtimestamp(i[1])}</b>\n" \
                       f"{i[3]}\n" \
                       f"<u>{i[2]}</u>\n"
            await call.message.answer(new_send)
            # отправка новостей в чат пользователю
    else:
        await call.message.answer("Новостей из этого сообщества нет.")


@dp.callback_query_handler(text=["buttonTC", "buttonITF", "buttonIASF",
                                 "buttonOKK", "buttonNF", "buttonINVIW", "buttonNIR", "buttonVRAR"])
async def sub_to_news_on_hash(call: types.CallbackQuery):
    """
    Данная функция используется для подписки на рассылку по хэштэгу
    """
    button = BUT_AND_HASH[call.data]
    id_player = call.from_user.id
    check_save = can.execute("""SELECT * FROM users WHERE iduser = ? """,
                             (int(id_player),)).fetchone()
    if isinstance(check_save, tuple):
        # если пользователь присутствует в базе пользователей
        sub = [str(i) for i in check_save[1].split()]
        # подписки пользователя
        if button in sub:
            await call.message.answer(f'Вы уже подписаны на рассылку по {button}')
            # сообщение, если пользователь уже подписан на данную рассылку
        else:
            update = """Update users set subscibes = ? where iduser = {}""".format(id_player)
            sub.append(button)
            can.execute(update, (str(" ".join(sub)),))
            can.commit()
            # если у пользователя уже есть другие подписки,
            # то обновляем список подписок новым хэштэгом
            await call.message.answer(f'Вы подписались на рассылку по {button}')
    else:
        info = [tuple([int(id_player), str(button)])]
        can.executemany("INSERT INTO users VALUES(?, ?)", info)
        can.commit()
        # добавляем пользователя в базу, сохраняя его id и хэштэг для рассылки
        await call.message.answer(f'Вы подписались на рассылку по {button}')

"""
Данные функции используется для вывода информации о хэштэге,
 3 новостей и подписки на рассылку
"""


@dp.message_handler(commands="TechnoCom")
@dp.message_handler(Text(equals="#TechnoCom"))
async def sub_and_news_tc(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonTC')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsTC'))
    await message.answer("""<b>Международный конкурс детских инженерных команд</b>
https://vk.com/technocom2022""", reply_markup=keyboard_tc)


@dp.message_handler(commands="ITfest_2022")
@dp.message_handler(Text(equals="#ITfest_2022"))
async def sub_and_news_itf(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonITF')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsITF'))
    await message.answer("""<b>Международный фестиваль информационных технологий «ITфест»</b>
https://vk.com/itfest2022""", reply_markup=keyboard_tc)


@dp.message_handler(commands="IASF2022")
@dp.message_handler(text="#IASF2022")
async def sub_and_news_iasf(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonIASF')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsIASF'))
    await message.answer("""<b>Международный аэрокосмический фестиваль</b>
https://vk.com/aerospaceproject""", reply_markup=keyboard_tc)


@dp.message_handler(commands="okk_fest")
@dp.message_handler(text="#ФестивальОКК")
async def sub_and_news_okk(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonOKK')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsOKK'))
    await message.answer("""<b>Всероссийский фестиваль общекультурных компетенций</b>
https://vk.com/okk_fest""", reply_markup=keyboard_tc)


@dp.message_handler(commands="Neurofest")
@dp.message_handler(text="#Нейрофест")
async def sub_and_news_nf(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonNF')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsNF'))
    await message.answer("""<b>Всероссийский фестиваль нейротехнологий «Нейрофест»</b>
https://vk.com/neurofest2022""", reply_markup=keyboard_tc)


@dp.message_handler(commands="Invisible_World")
@dp.message_handler(text="#НевидимыйМир")
async def sub_and_news_inviw(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonINVIW')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsINVIW'))
    await message.answer("""<b>Всероссийский конкурс по микробиологии «Невидимый мир»</b>
https://vk.com/nauchim.online""", reply_markup=keyboard_tc)


@dp.message_handler(commands="competitionNIR")
@dp.message_handler(text="#КонкурсНИР")
async def sub_and_news_nir(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonNIR')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsNIR'))
    await message.answer("""<b>Всероссийский конкурс научноисследовательских работ</b>
https://vk.com/nauchim.online""", reply_markup=keyboard_tc)


@dp.message_handler(commands="VRARFest3D")
@dp.message_handler(text="#VRARFest3D")
async def sub_and_news_vrar(message: types.Message):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data='buttonVRAR')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data='butnewsVRAR'))
    await message.answer(
        """<b>Международный фестиваль 3Dмоделирования и программирования VRAR-Fest</b>
https://vk.com/nauchim.online""", reply_markup=keyboard_tc)


@dp.message_handler(Text(equals="Подпишись на новости"))
async def hashtags(message: types.Message):
    """
    Данная функция используется при создании кнопок клавитуры
    для удобного перемещения по хэштэгам
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        types.KeyboardButton(text="#TechnoCom"),
        types.KeyboardButton(text="#ITfest_2022"),
        types.KeyboardButton(text="#IASF2022"),
        types.KeyboardButton(text="#ФестивальОКК"),
        types.KeyboardButton(text="#Нейрофест"),
        types.KeyboardButton(text="#НевидимыйМир"),
        types.KeyboardButton(text="#КонкурсНИР"),
        types.KeyboardButton(text="#VRARFest3D"),
        types.KeyboardButton(text="Вернуться")
    )
    await message.answer("Нажми на интересующий хэштэг для получения информации, "
                         "подписки на новости и 3 последних новости",
                         reply_markup=keyboard)


async def job():
    """
    Функция для рассылки новостей подпищикам мероприятий
    """
    print("Я working...")
    news = parsing_domins()
    if bool(news):
        # если появились новые новости
        users = can.execute("""SELECT * FROM users """).fetchall()
        for new in news:
            hash_new = new[1].split()
            # хэштэги новости
            for user in users:
                hash_user = user[1].split()
                # подписки пользователя
                for i in hash_new:
                    if i in hash_user:
                        # если хэштэг новости есть в подписках пользователя,
                        # то отправляем ему новость
                        try:
                            new_send = f"<b>Новость по вашей подписке на {i}</b>\n" \
                                       f"<b>{datetime.datetime.fromtimestamp(new[0])}</b>\n" \
                                       f"{new[3]}\n" \
                                       f"<u>{new[2]}</u>\n"
                            await bot.send_message(str(user[0]), new_send)
                        except BotBlocked:
                            print("Данный пользователь заблокировал бота")
                            # если пользователей заблокировал бота


async def scheduler():
    """
    Функция - таймер
    """
    aioschedule.every(10).minutes.do(job)
    # каждые 10 минут запускаем фунцию "job"
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
