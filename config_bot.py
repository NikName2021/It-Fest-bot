import psycopg2
import os

VERS = 5.131
PASSWORD_FOR_ADMIN = os.getenv('PASSWORD_FOR_ADMIN')
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN_VK = os.getenv('TOKEN_VK')
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print('You have forgot to set BOT_TOKEN')
    quit()

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')


# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT'))

# database connection
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()
