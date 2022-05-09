import asyncio
import datetime
import sqlite3
import logging
import aioschedule
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.executor import start_webhook
from config_bot import (BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH,
                          WEBAPP_HOST, WEBAPP_PORT, PASSWORD_FOR_ADMIN)
from config_bot import BOT_TOKEN, PASSWORD_FOR_ADMIN, conn, cur
from database import parsing_domins, add_new_domain

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
conn.autocommit = True
cur.execute("""SELECT name FROM info_hashtag """)
load_hashtags = [i[0] for i in cur.fetchall()]
cur.execute("""SELECT command FROM info_hashtag """)
load_commands = [i[0] for i in cur.fetchall()]
cur.execute("""SELECT name, command FROM info_hashtag """)
hash_unsub = {i[0]: f'/unsub_{i[1]}' for i in cur.fetchall()}
cur.execute("""SELECT name, short_for_sub FROM info_hashtag """)
but_and_news = {f'butnews{i[1]}': i[0] for i in cur.fetchall()}
cur.execute("""SELECT name, short_for_sub FROM info_hashtag """)
but_and_hash = {f'button{i[1]}': i[0] for i in cur.fetchall()}


class Admin(StatesGroup):
    waiting_password = State()
    domain = State()


class Newhashtag(StatesGroup):
    hashtag = State()
    command_for_hashtag = State()
    short_but = State()
    about_hashtag = State()
    url_hashtag = State()
    yes_or_no = State()


class Globmessage(StatesGroup):
    info_message = State()
    yes_or_no = State()


class Load(BoundFilter):
    async def check(self, message: types.Message):
        if "#" in message.text:
            if message.text in load_hashtags:
                return True
        else:
            if message.text[1:] in load_commands:
                return True
        return False


class Loadunsub(BoundFilter):
    async def check(self, message: types.Message):
        if message.text[1:] in [i[1:] for i in hash_unsub.values()]:
            return True
        return False


class Loadnews(BoundFilter):
    async def check(self, call: types.CallbackQuery):
        if call.data in [i for i in but_and_news.keys()]:
            return True
        return False


class Loadsub(BoundFilter):
    async def check(self, call: types.CallbackQuery):
        if call.data in but_and_hash.keys():
            return True
        return False


async def sub_users(id_player):
    cur.execute(f"SELECT * FROM users WHERE iduser = {int(id_player)} ")
    check_save = cur.fetchone()
    if isinstance(check_save, tuple):
        return check_save[1]


async def check_status(id_us):
    cur.execute(f"SELECT * FROM users WHERE iduser = {int(id_us)}")
    check_save = cur.fetchone()
    if isinstance(check_save, tuple) and check_save[2] == "admin":
        return "admin"


async def varible():
    global load_hashtags
    global load_commands
    global hash_unsub
    global but_and_hash
    global but_and_news
    cur.execute("""SELECT name FROM info_hashtag """)
    load_hashtags = [i[0] for i in cur.fetchall()]
    cur.execute("""SELECT command FROM info_hashtag """)
    load_commands = [i[0] for i in cur.fetchall()]
    cur.execute("""SELECT name, command FROM info_hashtag """)
    hash_unsub = {i[0]: f'/unsub_{i[1]}' for i in cur.fetchall()}
    cur.execute("""SELECT name, short_for_sub FROM info_hashtag """)
    but_and_news = {f'butnews{i[1]}': i[0] for i in cur.fetchall()}
    cur.execute("""SELECT name, short_for_sub FROM info_hashtag """)
    but_and_hash = {f'button{i[1]}': i[0] for i in cur.fetchall()}


async def job():
    """
    Функция для рассылки новостей подпищикам мероприятий
    """
    print("Я working...")
    news = await parsing_domins()
    if bool(news):
        # если появились новые новости
        cur.execute("""SELECT * FROM users """)
        users = cur.fetchall()
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


@dp.message_handler(Text(equals="Вернуться"))
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    """
    Данная функция используется для приветственной фразы и создания кнопок клавиатуры
    """
    button_1 = types.KeyboardButton(text="Последние 10 новостей")
    button_2 = types.KeyboardButton(text="Подпишись на новости")
    button_mysubs = KeyboardButton(text='Мои подписки')
    button_contact = KeyboardButton(text='Контакты')
    if await check_status(message.from_user.id) == "admin":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            button_mysubs, button_2)
        keyboard.add(button_1, KeyboardButton(text='Команды admin'))
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            button_mysubs, button_2)
        keyboard.add(button_contact, button_1)
    await message.answer("""Привет! Это телеграмм бот по хэштэгам!
Для справки и помощи по командам бота, нажми на /help""", reply_markup=keyboard)


@dp.message_handler(commands="help")
async def help_user(message: types.Message):
    sub = '\n'.join([f"/{i}" for i in load_commands])
    un_sub = '\n'.join([f"/unsub_{i}" for i in load_commands])
    await message.answer(f"""<b>Это справочник по командам бота.</b>
Перезапуск бота, нажми /start  
Вывод контактов организатора, нажми /contacts
Вывод подписок на мероприятия, нажми /mysubs
Для подписки на мероприятия и вывода 3 новостей нажми:
{sub}
Отписаться от всех новостей мероприятия
/all_unsub
Отписаться от новостей любого мероприятия:
{un_sub}""")


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
    check_save = await sub_users(id_player)
    # достаем информацию по пользователю из базы данных
    if check_save:
        subs = '\n'.join([str(i) for i in check_save.split()])
        un_command = '\n'.join([hash_unsub[i] for i in [str(i) for i in check_save.split()]])
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
    check_save = await sub_users(id_player)
    # достаем информацию по пользователю из базы данных
    if check_save:
        cur.execute(f"Delete from users where iduser = {id_player}")
        # удаляем всю информацию о пользователе из базы
        await message.answer('Вы отписались от всех рассылок')
    else:
        await message.answer('<b>Вы не подписаны ни на одно сообщество</b>')


@dp.message_handler(Loadunsub())
async def unsub_on_hash(message: types.Message):
    """
    Данная функция используется для отписки от определенной рассылки
    """
    id_player = message.from_user.id
    check_save = await sub_users(id_player)
    if check_save:
        sub = [str(i) for i in check_save.split()]
        # подписки пользователя
        hash_sub = [i for i, v in hash_unsub.items() if v == message.text][0]
        if hash_sub in sub:
            sub.remove(hash_sub)
            if not bool(sub):
                cur.execute(f"Delete from users where iduser = {id_player}")
                # полное удаление пользователя, если он отписался от единственной рассылки
            else:
                update = f"""Update users set subscibes = %s where iduser = %s"""
                cur.execute(update, (" ".join(sub), id_player))
                # изменение подписок пользователя
            conn.commit()
            await message.answer(f'Вы отписались от рассылки по {hash_sub}')
        else:
            await message.answer('Вы не подписаны на данную рассылку')
    else:
        await message.answer('<b>Вы не подписаны ни на одно сообщество</b>')


@dp.message_handler(Text(equals="Последние 10 новостей"))
async def get_10_news(message: types.Message):
    cur.execute('SELECT * FROM need_post ORDER BY time DESC')
    rec = cur.fetchall()[:10]
    for i in rec:
        news = f"<b>{datetime.datetime.fromtimestamp(i[1])}</b>\n" \
                       f"{i[4]}\n" \
                       f"<u>{i[3]}</u>\n"
        await message.answer(news)
        # отправка 10 новостей по всем хэштэгам  в чат пользователю


@dp.callback_query_handler(Loadnews())
async def send_news(call: types.CallbackQuery):
    """
    Данная функция используется для вывода 3 новостей по определенному хэштэгу
    """
    news = []
    received_button = call.data
    cur.execute("SELECT * FROM need_post ORDER BY time DESC")
    updates = cur.fetchall()
    # запрос новостей из базы данных
    hash_sub = but_and_news[received_button]
    for update in updates:
        if hash_sub in update[2].split():
            news.append(update)
        if len(news) == 3:
            break
        # подбор  последних 3 новостей по запрошенному хэштэгу"
    if bool(news):
        for i in news:
            new_send = f"<b>{datetime.datetime.fromtimestamp(i[1])}</b>\n" \
                       f"{i[4]}\n" \
                       f"<u>{i[3]}</u>\n"
            await call.message.answer(new_send)
            # отправка новостей в чат пользователю
    else:
        await call.message.answer("Новостей из этого сообщества нет.")


@dp.callback_query_handler(Loadsub())
async def sub_to_news_on_hash(call: types.CallbackQuery):
    """
    Данная функция используется для подписки на рассылку по хэштэгу
    """
    button = but_and_hash[call.data]
    id_player = call.from_user.id
    check_save = await sub_users(id_player)
    if check_save:
        # если пользователь присутствует в базе пользователей
        sub = [str(i) for i in check_save.split()]
        # подписки пользователя
        if button in sub:
            await call.message.answer(f'Вы уже подписаны на рассылку по {button}')
            # сообщение, если пользователь уже подписан на данную рассылку
        else:
            sub.append(button)
            update = f"""Update users set subscibes = %s where iduser = %s"""
            cur.execute(update, (" ".join(sub), int(id_player)))
            # если у пользователя уже есть другие подписки,
            # то обновляем список подписок новым хэштэгом
            await call.message.answer(f'Вы подписались на рассылку по {button}')
    else:
        info = tuple([int(id_player), button, 'user'])
        cur.execute("INSERT INTO users VALUES(%s, %s, %s)", (int(id_player), button, 'user'))
        # добавляем пользователя в базу, сохраняя его id и хэштэг для рассылки
        await call.message.answer(f'Вы подписались на рассылку по {button}')


@dp.message_handler(Text(equals="Прошлая клавиатура"))
@dp.message_handler(Text(equals="Подпишись на новости"))
async def st_hashtags(message: types.Message):
    """
    Данная функция используется при создании кнопок клавитуры
    для удобного перемещения по хэштэгам
    """
    cur.execute(f"SELECT * FROM info_hashtag WHERE Status = 'NONE'")
    check_save = [i[0] for i in cur.fetchall()]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        *[types.KeyboardButton(text=i) for i in check_save],
        types.KeyboardButton(text="Добавленные хэштэги"),
        types.KeyboardButton(text="Вернуться")
    )
    await message.answer("Нажми на интересующий хэштэг для получения информации, "
                         "подписки на новости и 3 последних новости",
                         reply_markup=keyboard)


@dp.message_handler(text="Добавленные хэштэги")
async def adden_hashtags(message: types.Message):
    cur.execute(f"SELECT * FROM info_hashtag WHERE Status = 'YES'")
    check_save = [i[0] for i in cur.fetchall()]
    if bool(check_save):
        keyboard_hs = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            *[types.KeyboardButton(text=i) for i in check_save],
            types.KeyboardButton(text="Прошлая клавиатура")
        )
        # поменять 332
        await message.answer("Хэштэги добавленные админом группы",
                             reply_markup=keyboard_hs)
    else:
        await message.answer("Администратор еще не добавил ни одного дополнительного хэштэга")


@dp.message_handler(Load())
async def sub_and_news(message: types.Message):
    if "/" in message.text:
        cur.execute(f"SELECT * FROM info_hashtag WHERE command = '{message.text[1:]}'")
    else:
        cur.execute(f"SELECT * FROM info_hashtag WHERE name = '{message.text}'")
    check_save = cur.fetchone()
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Подписаться', callback_data=f'button{check_save[2]}')).add(
        InlineKeyboardButton('Последние 3 новости', callback_data=f'butnews{check_save[2]}'))
    await message.answer(f"""<b>{check_save[3]}</b>
{check_save[4]}""", reply_markup=keyboard_tc)

#              ********************************
# ******************* ADMIN Commands ********************************************
#              ********************************


@dp.message_handler(Text(equals='Доп.команды'))
@dp.message_handler(commands="help_admin")
async def help_admin(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        await message.answer("""<b>Это справочник по командам бота для админа.</b>
Перезапуск бота, нажми /start  
Вывод контактов организатора, нажми ...
Вывод подписок на мероприятия, нажми ...
Для подписки на мероприятия и вывода 3 новостей нажми:
/global_message
/un_admin""")
    else:
        await message.answer("Нет прав на данную команду")


@dp.message_handler(commands="cancel", state="*")
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Еще не начат ввод даннных")
        return
    await state.finish()
    await message.answer("Ввод отменен")


@dp.message_handler(Text(equals='Команды admin'))
async def commands_admin(message: types.Message):
    """
    Данная функция используется для приветственной фразы и создания кнопок клавиатуры
    """
    add_hashtag = KeyboardButton(text="Добавить хэштэг")
    add_domen = KeyboardButton(text="Добавить доменн")
    button_add = KeyboardButton(text='Добавленное')
    button_help = KeyboardButton(text="Доп.команды")
    if await check_status(message.from_user.id) == "admin":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            add_domen, add_hashtag)
        keyboard.add(button_help, button_add)
        keyboard.add(KeyboardButton(text="Вернуться"))
    else:
        await message.answer("Ты не являешься админом")
        return
    await message.answer("""Команды admin""", reply_markup=keyboard)


@dp.message_handler(commands="admin")
async def admin(message: types.Message):
    await Admin.waiting_password.set()
    await message.answer("Введи пароль:")


@dp.message_handler(state=Admin.waiting_password)
async def becoming_an_admin(message: types.Message, state: FSMContext):
    if message.text == PASSWORD_FOR_ADMIN:
        id_player = message.from_user.id
        cur.execute(f"SELECT * FROM users WHERE iduser = {int(id_player)}")
        check_save = cur.fetchone()
        if isinstance(check_save, tuple):
            if check_save[2] == "user":
                update = f"""Update users set status = %s where iduser = %s"""
                cur.execute(update, ('admin', int(id_player)))
                await message.answer("""Теперь вы имеете права админа и вам доступны новые команды.
Чтобы увидить новые команды,
нажми /help_admin. 
<b>Рекомендуем перезапустить бота по команде /start</b>""")
            elif check_save[2] == 'admin':
                await message.answer('Ты уже являешься админом')
        else:
            cur.execute("INSERT INTO users VALUES(%s, %s, %s)", (int(id_player), "", 'admin'))
            await message.answer("""Теперь вы имеете права админа и вам доступны новые команды.
Чтобы увидить новые команды,
нажми /help_admin. 
<b>Рекомендуем перезапустить бота по команде /start</b>""")
    else:
        await message.reply("Пароль неверный! Если хочешь попробовать снова, введи /admin")
    await state.finish()


@dp.message_handler(commands="un_admin")
async def un_admin(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        update = f"""Update users set status = %s where iduser = %s"""
        conn.execute(update, ("user", message.from_user.id))
        conn.commit()
        await message.answer('''Теперь ты юзер.
<b>Рекомендуем перезапустить бота по команде /start</b>''')
    else:
        await message.answer('Нет прав на данную команду')


@dp.message_handler(Text(equals="Добавить доменн"))
@dp.message_handler(commands="add_domain")
async def add_domain_to_bd(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        await Admin.domain.set()
        await message.answer("Введи доменн:")
    else:
        await message.answer("Ты не являешься админом")


@dp.message_handler(state=Admin.domain)
async def check_domain(message: types.Message, state: FSMContext):
    ans = await add_new_domain(message.text)
    if ans is None:
        await message.answer("Ошибка доступ к доменну. Попробуйте снова, изменив доменн.")
    elif ans is False:
        await message.answer("Максимальное число доменнов 20.")
    elif ans == "Exists":
        await message.answer("Такой доменн уже существует в системе")
    elif ans is True:
        await message.answer("Доменн успешно добавлен в список отслеживания")
    await state.finish()


@dp.message_handler(Text(equals="Добавить хэштэг"))
@dp.message_handler(commands="new_hashtag")
async def add_hashtag_to_bd(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        if len(load_hashtags) == 20:
            await message.answer("Максимальное количество хэштэгов для подписки 20")
        else:
            await Newhashtag.hashtag.set()
            await message.answer("Введи новый хэштэг #инструкция:")
    else:
        await message.answer("Ты не являешься админом")


@dp.message_handler(state=Newhashtag.hashtag)
async def add_hashtag_stage2(message: types.Message, state: FSMContext):
    print(load_hashtags)
    if message.text in load_hashtags:
        await message.answer("Такой хэштэг уже есть в системе, попробуй снова")
        await asyncio.sleep(1)
    elif message.text[:1] != "#":
        await message.answer("Не найдена решетка(#) в хэштэге, попробуй снова")
        await asyncio.sleep(1)
    else:
        async with state.proxy() as data:
            data["hashtag"] = message.text
        await Newhashtag.next()
        await message.answer("Теперь введи команду по хэштэгу"
                             " для пользователей(используй только латинский алфавит)"
                             "#инструкция")


@dp.message_handler(state=Newhashtag.command_for_hashtag)
async def add_hashtag_stage3(message: types.Message, state: FSMContext):
    if message.text in load_commands:
        await message.answer("Такая команда уже есть в системе, попробуй снова")
        await asyncio.sleep(1)
    if re.search(r'[^a-zA-Z _]', message.text):
        await message.reply("Команда не соответствует условию, попробуй снова")
        await asyncio.sleep(1)
    else:
        async with state.proxy() as data:
            data["command"] = message.text
        await Newhashtag.next()
        await message.answer("Теперь введи Префикс"
                             "#инструкция")


@dp.message_handler(state=Newhashtag.short_but)
async def add_hashtag_stage4(message: types.Message, state: FSMContext):
    cur.execute("SELECT short_for_sub FROM info_hashtag")
    check = cur.fetchall()
    if message.text in [i[0] for i in check]:
        await message.answer("Такой префикс уже есть в системе, попробуй снова")
        await asyncio.sleep(1)
    elif re.search(r'[^a-zA-Z]', message.text):
        await message.reply("Команда не соответствует условию, попробуй снова")
        await asyncio.sleep(1)
    else:
        async with state.proxy() as data:
            data["short"] = message.text.upper()
        await Newhashtag.next()
        await message.answer("Осталось немного. Введи описание для хэштэга"
                             "#инструкция")


@dp.message_handler(state=Newhashtag.about_hashtag)
async def add_hashtag_stage5(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["info"] = message.text
    await Newhashtag.next()
    await message.answer("Осталось немного. Введи ссылку на сообщество,"
                         " где можно найти события по хэштэгу"
                         "#инструкция")


@dp.message_handler(state=Newhashtag.url_hashtag)
async def add_hashtag_stage6(message: types.Message, state: FSMContext):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Да', callback_data='yes'),
        InlineKeyboardButton('Нет', callback_data='no'))
    async with state.proxy() as data:
        data["url"] = message.text
    async with state.proxy() as data:
        await message.answer(f"""
<b>Подтвердите введенные данные:</b>
Новый хэштэг: <b>{data["hashtag"]}</b>
Команда для пользователей: <b>{data["command"]}</b>
Сокращение: <b>{data["short"]}</b>
Описание: <b>{data["info"]}</b>
Ссылка: <b>{data["url"]}</b>
Для подтверждения добавления хэштэга, выбери <b>'да'</b>
Для отмены добавления, выбери <b>'нет'</b>""", reply_markup=keyboard_tc)
    await Newhashtag.next()


@dp.callback_query_handler(state=Newhashtag.yes_or_no, text=["yes", "no"])
async def add_hashtag_stage7(call: types.CallbackQuery, state: FSMContext):
    if call.data == "yes":
        async with state.proxy() as data:
            cur.execute(
                "INSERT INTO info_hashtag VALUES(%s, %s, %s, %s, %s, %s)",
                (data["hashtag"], data["command"],
                  data["short"], data["info"],
                  data["url"], "YES")
            )
        await varible()
        await call.message.answer("Хэштэг успешно добавлен")
        await state.finish()
    elif call.data == "no":
        await call.message.answer("Ввод отменен, данные удалены")
        await state.finish()


@dp.message_handler(commands='global_message')
async def global_message(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        await Globmessage.info_message.set()
        await message.answer("Это функция отправки вашего сообщения всем подписчикам бота."
                             "Так вы можете уведомить подписчиков о"
                             " добавление или удаление хэштэга или же домена, а также о обновлениях бота."
                             "<b>!Будьте осторожны с этой функцией.!</b>")
    else:
        await message.answer("Ты не являешься админом")


@dp.message_handler(state=Globmessage.info_message)
async def preview_global_message(message: types.Message, state: FSMContext):
    keyboard_tc = InlineKeyboardMarkup(resize_keyboard=True).add(
        InlineKeyboardButton('Да', callback_data='yes'),
        InlineKeyboardButton('Нет', callback_data='no'))
    async with state.proxy() as data:
        data["message"] = message.text
    await message.answer(f"""
<b>Предпросмотр сообщения:</b>
<b> Сообщение от администратора группы </b>
{message.text}
Для подтверждения отправки сообщения, выбери <b>'да'</b>
Для отмены отправки, выбери <b>'нет'</b>""", reply_markup=keyboard_tc)
    await Globmessage.next()


@dp.callback_query_handler(state=Globmessage.yes_or_no, text=["yes", "no"])
async def send_global_message(call: types.CallbackQuery, state: FSMContext):
    if call.data == "yes":
        async with state.proxy() as data:
            cur.execute("""SELECT * FROM users """)
            users = cur.fetchall()
            for user in users:
                try:
                    new_send = f"""<b> Сообщение от администратора группы </b>
{data['message']}"""
                    await bot.send_message(str(user[0]), new_send)
                except BotBlocked:
                    print("Данный пользователь заблокировал бота")
        await call.message.answer("Рассылка успешно завершена")
        await state.finish()
    elif call.data == "no":
        await call.message.answer("Отправка отменена, данные удалены")
        await state.finish()


@dp.message_handler(Text(equals="Добавленное"))
async def added_admin(message: types.Message):
    if await check_status(message.from_user.id) == "admin":
        cur.execute(f"SELECT name FROM info_hashtag WHERE status = '{'YES'}'")
        check_hashtag = [i[0] for i in cur.fetchall()]
        cur.execute(f"SELECT domain FROM domains WHERE status = '{'YES'}'")
        check_domain = [i[0] for i in cur.fetchall()]
        hs = '\n'.join(check_hashtag)
        dom = '\n'.join(f"{i} \n(https://vk.com/{i})" for i in check_domain)
        await message.answer(f"""<b>Добавленные хэштэги:</b>
{hs}
<b>Добавленные доменны:</b>
{dom}""")

    else:
        await message.answer("Ты не являешься админом")


@dp.message_handler(content_types=types.ContentTypes.PHOTO)
async def everything_else(msg: types.Message):
    await msg.answer('Красивенько 😍')


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def if_the_photo(msg: types.Message):
    await msg.answer('Неизвестная для меня команда :(')


async def scheduler():
    """
    Функция - таймер
    """
    aioschedule.every(10).minutes.do(job)
    # каждые 10 минут запускаем фунцию "job"
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    asyncio.create_task(scheduler())
    dp.filters_factory.bind(Load)
    dp.filters_factory.bind(Loadnews)
    dp.filters_factory.bind(Loadunsub)
    dp.filters_factory.bind(Loadsub)


async def on_shutdown(dp):
    cur.close()
    conn.close()
    await bot.delete_webhook()


# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=False, on_startup=on_startup)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
