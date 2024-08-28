import logging
import os
from textwrap import dedent

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram.ext import Updater

from custom_validators import is_float
from strapi import get_products, get_product_and_picture, get_product_image, get_cart, create_cart, add_product_to_cart, \
    delete_cart_product, get_user, save_email

_database = None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = int(os.getenv("DATABASE_PORT"))
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def show_cart(update, context, strapi_access_token, strapi_url):
    telegram_id = context.bot_data['user_id']
    user_cart = get_cart(
        telegram_id,
        strapi_token=strapi_access_token,
        strapi_url=strapi_url
    )
    user_cart_data = user_cart['data'][0]
    context.bot_data['cart_id'] = user_cart_data['id']
    cart_products = user_cart_data['attributes']['cart_products']['data']
    total = 0
    cart_text = ''
    inline_keyboard = [
        [InlineKeyboardButton('Оплатить', callback_data='pay')],
        [InlineKeyboardButton('В меню', callback_data='back_to_menu')],
    ]
    for cart_product in cart_products:
        cart_product_id = cart_product['id']
        product_data = cart_product['attributes']['product']['data']
        product_name = product_data['attributes']['name']
        product_description = product_data['attributes']['description']
        product_price = product_data['attributes']['price']
        product_weight = cart_product['attributes']['weight']
        product_total = product_price * product_weight
        total += product_total
        cart_text += f"""
        {product_name}
        {product_description}
        {product_price:.2f} рублей за кг
        {product_weight}кг в корзине за {product_total:.2f} рублей

        """
        inline_keyboard.append(
            [InlineKeyboardButton(
                f'Убрать {product_name} за {product_total:.2f} рублей', callback_data=f'delete_{cart_product_id}'
            )]
        )
    cart_text += f'Сумма: {total:.2f} рублей'
    cart_text = dedent(cart_text)
    context.bot.send_message(
        context.bot_data['user_id'],
        cart_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
    )
    return 'HANDLE_CART'


def start(update, context, strapi_access_token, strapi_url):
    update.message.reply_text(
        text='Привет!',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton('Моя корзина')]]),
    )
    context.bot_data['user_id'] = str(update.message.from_user.id)
    return get_menu(update, context, strapi_access_token, strapi_url)


def get_user_contacts(update, context, strapi_access_token, strapi_url):
    cart_id = context.bot_data['cart_id']
    user = get_user(cart_id, strapi_url, strapi_access_token)

    user_id = user[0]['id']
    email = update.message.text
    try:
        save_email(user_id, email, strapi_url, strapi_access_token)
    except:
        update.message.reply_text('Неверная почта')
        return 'WAITING_EMAIL'
    return 'START'


def get_menu(update, context, strapi_access_token, strapi_url):
    keyboard = get_products_keyboard(strapi_access_token, strapi_url)
    user_id = context.bot_data['user_id']
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        user_id,
        'Пожалуйста выберите:',
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
        )]
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
    user_id = context.bot_data['user_id']
    cart = get_cart(user_id, strapi_url, strapi_access_token)

    if not cart.get('data'):
        create_cart(user_id, strapi_url, strapi_access_token)
        cart = get_cart(user_id, strapi_url, strapi_access_token)
    cart_id = cart['data'][0]['id']

    return cart_id


def handle_cart(update, context, strapi_access_token, strapi_url):
    query_data = update.callback_query.data
    if query_data.split('_')[0] == 'delete':
        cart_product_id = query_data.split('_')[1]
        delete_cart_product(cart_product_id, strapi_url, strapi_access_token)

        show_cart(update, context, strapi_access_token, strapi_url)
        update.callback_query.delete_message()
    return 'HANDLE_DESCRIPTION'


def handle_description(update, context, strapi_access_token, strapi_url):
    query_data = update.callback_query.data
    if query_data == 'back_to_menu':
        return get_menu(update, context, strapi_access_token, strapi_url)
    elif query_data == 'add_to_cart':
        cart_id = get_or_create_cart(update, context, strapi_access_token, strapi_url)
        context.bot_data['cart_id'] = cart_id
        user_id = context.bot_data['user_id']

        context.bot.send_message(
            user_id,
            'Сколько килограмм вам?'
        )
        return 'HANDLE_WEIGHT'
    elif query_data == 'pay':
        context.bot.send_message(
            update.callback_query.from_user.id,
            'Введите email',
        )
        return 'WAITING_EMAIL'


def handle_weight(update, context, strapi_access_token, strapi_url):
    is_weight = is_float(update.message)

    if not is_weight:
        update.message.reply_text("Пожалуйста, введите количество в килограммах.")
        return 'HANDLE_WEIGHT'

    weight = float(update.message.text)
    cart_id = context.bot_data['cart_id']
    product_id = context.bot_data['product_id']
    add_product_to_cart(
        cart_id=cart_id,
        product_id=product_id,
        weight=weight,
        strapi_url=strapi_url,
        strapi_token=strapi_access_token

    )
    update.message.reply_text("Продукт был успешно добавлен в вашу корзину")

    return 'START'


def handle_users_reply(update, context):
    db = get_database_connection()
    strapi_access_token = context.bot_data.get('strapi_access_token')
    strapi_url = context.bot_data.get('strapi_url')

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
    elif user_reply == 'Моя корзина':
        next_state = show_cart(update, context, strapi_access_token, strapi_url)
        db.set(chat_id, next_state)
        return
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_WEIGHT': handle_weight,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': get_user_contacts,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context, strapi_access_token, strapi_url)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.exception(err)


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

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))

    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_users_reply))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
