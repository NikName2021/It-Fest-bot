import sqlite3
import re
import requests
from config import token, vers, domains, check_hash


def save_all_post(posts_card, domain):
    """Функция для сохранения всех постов в sql базу данных"""
    conn = sqlite3.connect('Posts.db')
    cur = conn.cursor()
    saves = []
    need_post = []
    if domain == "nauchim.online":
        search = "INSERT INTO {} VALUES(NULL, ?, ?, ?, ?)".format("nauchim_online")
        check = 'SELECT * FROM {} WHERE time = ?'.format("nauchim_online")
    else:
        search = "INSERT INTO {} VALUES(NULL, ?, ?, ?, ?)".format(domain)
        check = 'SELECT * FROM {} WHERE time = ?'.format(domain)

    for post in posts_card:
        check_save = cur.execute(check, (post["date"], ))
        if check_save.fetchone() is None:
            # сохранение постов по таблицам
            saves.append(
                tuple([int(post["date"]), str(" ".join(re.findall(r'(#\S+)', post["text"]))),
                       str(f"https://vk.com/{domain}?w=wall{post['owner_id']}_{post['id']}"),
                       str(post["text"])])
            )
            print("Новая новость")
        for i in re.findall(r'(#\S+)', post["text"]):
            if i in check_hash:
                # сохранение постов с нужными хэштэгами в need_post sql
                if cur.execute("SELECT * FROM need_post WHERE time=?", (str(post["date"]), )).fetchone() is None:
                    need_post.append(
                        tuple([int(post["date"]),
                               str(" ".join(re.findall(r'(#\S+)', post["text"]))),
                               str(f"https://vk.com/{domain}?w=wall{post['owner_id']}_{post['id']}"),
                               str(post["text"])])
                    )

    cur.executemany("INSERT INTO need_post VALUES(NULL, ?, 'AKTIV', ?, ?, ?)", need_post)
    cur.executemany(search, saves)
    conn.commit()
    print("Выполнено")
    # возвращаем новые посты с нужными хэштэгами для рассылки бота
    return need_post


def parsing_domins():
    """Функция для запроса постов по доменам"""
    need_posts = []
    for domain in domains:
        response = requests.get("https://api.vk.com/method/wall.get",
                                params={
                                    "access_token": token,
                                    "v": vers,
                                    "domain": domain
                                }
                                )
        # делаем запрос на страницу сообщества и достаем от туда посты
        posts_card = response.json()["response"]["items"]
        for post in save_all_post(posts_card, domain):
            need_posts.append(post)
    return need_posts
