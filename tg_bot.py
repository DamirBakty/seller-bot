import logging
import os

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler
from telegram.ext import Updater

from strapi import get_products, get_product_and_picture, get_product_image, get_cart, create_cart

_database = None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, context, strapi_access_token, strapi_url):
    context.bot_data['user_id'] = update.message.from_user.id
    return get_menu(update, context, strapi_access_token, strapi_url)


def get_menu(update, context, strapi_access_token, strapi_url):
    keyboard = get_products_keyboard(strapi_access_token, strapi_url)
    user_id = context.bot_data['user_id']
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        user_id,
        'Please choose:',
        reply_markup=reply_markup,
    )
    return 'HANDLE_MENU'


def handle_menu(update, context, strapi_access_token, strapi_url):
    query = update.callback_query

    product_id = query.data
    context.bot_data['product_id'] = product_id

    product_details = get_product_details(strapi_access_token, product_id, strapi_url)
    product_text = product_details['text']
    product_image = product_details['image']

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Добавить в корзину',
            callback_data='add_to_cart'
        )],
        [InlineKeyboardButton(
            'Назад',
            callback_data='back_to_menu'
        )],
    ])

    context.bot.send_photo(
        update.callback_query.from_user.id,
        photo=product_image,
        caption=product_text,
        reply_markup=reply_markup

    )
    update.callback_query.delete_message()

    return 'HANDLE_DESCRIPTION'


def get_or_create_cart(update, context, strapi_access_token, strapi_url):
    product_id = context.bot_data['product_id']
    user_id = context.bot_data['user_id']
    cart = get_cart(user_id, strapi_url, strapi_access_token)

    if not cart:
        create_cart(user_id, strapi_url, strapi_access_token)
        cart = get_cart(user_id, strapi_url, strapi_access_token)
    cart_id = cart['data'][0]['id']


def handle_description(update, context, strapi_access_token, strapi_url):
    if update.callback_query.data == 'back_to_menu':
        return get_menu(update, context, strapi_access_token, strapi_url)


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
    strapi_access_token = context.bot_data.get('strapi_access_token')
    strapi_url = context.bot_data.get('strapi_url')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context, strapi_access_token, strapi_url)
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


def get_products_keyboard(strapi_token, strapi_url):
    products = get_products(strapi_url, strapi_token)

    keyboard = []
    for product in products['data']:
        keyboard.append(
            [InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])]
        )
    return keyboard


def get_product_details(strapi_token, product_id, strapi_url):
    product = get_product_and_picture(product_id, strapi_url, strapi_token)

    product_attributes = product['data']['attributes']
    product_image_link = product_attributes['image']['data']['attributes']['url']
    product_image = get_product_image(strapi_url, product_image_link)
    product_text = (
        f'{product_attributes["name"]} ({product_attributes["price"]} руб. за кг)\n\n'
        f'{product_attributes["description"]}'
    )
    return {
        'text': product_text,
        'image': product_image
    }


def main():
    env = Env()
    env.read_env()
    strapi_access_token = env.str('STRAPI_ACCESS_TOKEN')
    strapi_url = env.str('STRAPI_URL')

    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['strapi_access_token'] = strapi_access_token
    dispatcher.bot_data['strapi_url'] = strapi_url

    # dispatcher.add_handler(
    #     MessageHandler(Filters.regex(r'Моя корзина'), show_cart),
    # )
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))

    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
