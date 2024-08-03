import logging
import os

import redis
import requests
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram.ext import Updater

_database = None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, context):
    chat_id = update.message.chat_id
    strapi_access_token = context.bot_data.get('strapi_access_token')

    keyboard = get_products_keyboard(strapi_access_token)
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'BUTTON'


def button(update, context):
    query = update.callback_query
    strapi_access_token = context.bot_data.get('strapi_access_token')

    product_id = query.data
    # query.answer()
    get_product_details(strapi_access_token, product_id)
    # query.edit_message_text(text=f"Selected option: {query.data}")
    text = get_product_details(strapi_access_token, product_id)

    update.message.reply_text(text=text)

    return 'BUTTON'


def handle_users_reply(update, context):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'BUTTON': button
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.exception(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = int(os.getenv("DATABASE_PORT"))
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def get_products_keyboard(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get('http://localhost:1337/api/products', headers=headers)
    r.raise_for_status()

    products = r.json()

    keyboard = []
    for product in products['data']:
        keyboard.append(
            [InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])]
        )
    return keyboard


def get_product_details(access_token, product_id):
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get(f'http://localhost:1337/api/products/{product_id}', headers=headers)
    r.raise_for_status()

    product_details = r.json()['data']['attributes']

    text = f"""
    {product_details['name']} ({product_details['price']} руб. за кг)\n\n
    {product_details['description']}
    """
    return text


def main():
    env = Env()
    env.read_env()
    strapi_access_token = env.str('STRAPI_ACCESS_TOKEN')
    strapi_url = env.str('STRAPI_URL')

    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['strapi_access_token'] = strapi_access_token

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
