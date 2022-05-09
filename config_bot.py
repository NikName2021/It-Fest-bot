import psycopg2
import os
#
# PASSWORD_FOR_ADMIN = "telegrambot"
# BOT_TOKEN = '5199305489:AAH4jGBgsjahtS0eNKeaofBGqGMOXk_Tw4g'
# DATABASE_URL = "postgres://pcfuuqmqrcbusm:ce3d10a8b8e8c5edf078a1c6d97e377010037a877d49cd118dce49dff9b010a9@ec2-34-246-227-219.eu-west-1.compute.amazonaws.com:5432/dfgau9f8digql9"
# TOKEN_VK = "54f50cd254f50cd254f50cd2aa548efd28554f554f50cd236b32aa20ba369a98278896c"
# VERS = 5.131


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
