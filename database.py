import re
import requests
from config_bot import TOKEN_VK, VERS, conn, cur


async def save_all_post(posts_card, domain):
    """Функция для сохранения всех постов в sql базу данных"""
    saves = []
    need_post = []
    if domain == "nauchim.online":
        search = "INSERT INTO nauchim_online VALUES(%s, %s, %s, %s)"
        check = 'SELECT * FROM nauchim_online WHERE time = %s'
    else:
        search = f"INSERT INTO {domain} VALUES(%s, %s, %s, %s)"
        check = f'SELECT * FROM {domain} WHERE time = %s'
    cur.execute(f"""SELECT domain FROM domains WHERE status = '{"NONE"}'""")
    standart_dom = [i[0] for i in cur.fetchall()]
    cur.execute("SELECT name FROM info_hashtag ")
    load_hashtags = [i[0] for i in cur.fetchall()]
    for post in posts_card:
        if domain in standart_dom:
            check_save = cur.execute(check, [post["date"]])
            if check_save is not None:
                # сохранение постов по таблицам
                saves.append(
                    tuple([int(post["date"]), " ".join(re.findall(r'(#\S+)', post["text"])),
                           f"https://vk.com/{domain}?w=wall{post['owner_id']}_{post['id']}",
                           post["text"]])
                )
                print("Новая новость")
        find = re.findall(r'(#\S+)', post["text"])
        for i in find:
            if i in load_hashtags:
                # сохранение постов с нужными хэштэгами в need_post sql
                cur.execute(f"SELECT * FROM need_post WHERE time = {int(post['date'])}")
                if cur.fetchone() is None:
                    need_post.append(
                        tuple([int(post["date"]),
                               " ".join(find),
                               f"https://vk.com/{domain}?w=wall{post['owner_id']}_{post['id']}",
                               post["text"]])
                    )
                    print("Новая новость по хэштэгу")
    cur.executemany("INSERT INTO need_post VALUES(1, %s, %s, %s, %s)", need_post)
    if domain in standart_dom:
        cur.executemany(search, saves)
    conn.commit()
    print("Выполнено")
    # возвращаем новые посты с нужными хэштэгами для рассылки бота
    return need_post


async def parsing_domins():
    """Функция для запроса постов по доменам"""
    need_posts = []

    cur.execute("SELECT domain FROM domains")
    load_domains = [i[0] for i in cur.fetchall()]
    for domain in load_domains:
        response = requests.get("https://api.vk.com/method/wall.get",
                                params={
                                    "access_token": TOKEN_VK,
                                    "v": VERS,
                                    "domain": domain
                                }
                                )
        # делаем запрос на страницу сообщества и достаем от туда посты
        posts_card = response.json()["response"]["items"]
        for post in await save_all_post(posts_card, domain):
            need_posts.append(post)
    return need_posts


async def add_new_domain(domaint):
    """
        Функция проверки доменна и сохранения его в бд
    """
    cur.execute("SELECT domain FROM domains")
    load_domains = [i[0] for i in cur.fetchall()]
    if len(load_domains) == 20:
        # проверка на колличество сохраненных хэштэгов
        return False
    new_domain = domaint.split("/")[-1]
    response = requests.get("https://api.vk.com/method/wall.get",
                            params={
                                "access_token": TOKEN_VK,
                                "v": VERS,
                                "domain": new_domain
                            }
                            )
    if response.status_code in [404, 503, 500, 403]:
        return
    elif new_domain in load_domains:
        # проверка на то, что в бд еще нет такого хэштэга
        return "Exists"
    else:
        cur.execute("INSERT INTO domains VALUES(%s, %s)", (new_domain, 'YES'))
        conn.commit()
        return True