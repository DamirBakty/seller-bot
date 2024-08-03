import os
from io import BytesIO

import requests


def get_products():
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    response = requests.get(
        os.path.join(strapi_url, 'products'),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        }
    )
    response.raise_for_status()
    return response.json()


def add_product(cart_id, product_id, amount):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    payload = {
        'data': {
            'cart': cart_id,
            'product': product_id,
            'amount': amount,
        }
    }
    response = requests.post(
        os.path.join(strapi_url, 'product-in-carts'),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        json=payload
    )
    response.raise_for_status()


def get_cart_product(cart_id, product_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    cart_product_filter = {
        'filters[cart][$eq]': cart_id,
        'filters[product][$eq]': product_id,
    }
    response = requests.get(
        os.path.join(strapi_url, 'product-in-carts'),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=cart_product_filter,
    )
    response.raise_for_status()
    return response.json()


def get_cart(telegram_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    cart_filter = {
        'filters[tg_id][$eq]': telegram_id,
        'populate[cartproducts][populate]': 'product',
    }
    response = requests.get(
        os.path.join(os.getenv('STRAPI_API_URL'), 'carts'),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=cart_filter
    )
    response.raise_for_status()
    return response.json()


def create_cart(telegram_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    cart_payload = {
        'data': {'tg_id': telegram_id},
    }
    response = requests.post(
        os.path.join(strapi_url, 'carts'),
        headers={
            'Authorization': f'bearer {strapi_token}'
        },
        json=cart_payload
    )
    response.raise_for_status()
    return response.status_code


def delete_cart_product(product_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    response = requests.delete(
        os.path.join(
            strapi_url,
            'product-in-carts',
            str(product_id),
        ),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        }
    )
    response.raise_for_status()
    return response.status_code


def get_product_and_picture(product_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    payload = {
        'populate': 'picture'
    }

    response = requests.get(
        os.path.join(strapi_url, 'products', product_id),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=payload
    )
    response.raise_for_status()
    return response.json()


def get_user(cart_id):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    user_filter = {'filters[cart][$eq]': cart_id}
    response = requests.get(
        os.path.join(strapi_url, 'users'),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=user_filter,
    )
    response.raise_for_status()
    return response.json()


def save_email(user_id, email):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    strapi_token = os.getenv('STRAPI_TOKEN', None)
    payload = {'email': email}
    response = requests.put(
        os.path.join(strapi_url, 'users', str(user_id)),
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        json=payload
    )
    response.raise_for_status()
    return response.status_code


def download_picture(picture_url):
    strapi_url = os.getenv('STRAPI_URL', 'http://localhost:1337/api')
    picture_url = os.path.join(strapi_url[:-4], picture_url)
    response = requests.get(picture_url)
    response.raise_for_status()
    return BytesIO(response.content)
