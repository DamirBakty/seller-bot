from io import BytesIO

import requests


def get_products(strapi_url, strapi_token):
    response = requests.get(
        f'{strapi_url}/api/products',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        }
    )
    response.raise_for_status()
    return response.json()


def add_product(cart_id, product_id, amount, strapi_url, strapi_token):
    payload = {
        'data': {
            'cart': cart_id,
            'product': product_id,
            'amount': amount,
        }
    }
    response = requests.post(
        f'{strapi_url}/api/product-in-carts',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        json=payload
    )
    response.raise_for_status()


def get_cart_product(cart_id, product_id, strapi_url, strapi_token):
    cart_product_filter = {
        'filters[cart][$eq]': cart_id,
        'filters[product][$eq]': product_id,
    }
    response = requests.get(
        f'{strapi_url}/api/product-in-carts',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=cart_product_filter,
    )
    response.raise_for_status()
    return response.json()


def get_cart(telegram_id, strapi_url, strapi_token):
    cart_filter = {
        'filters[telegram_id][$eq]': telegram_id,
        'populate[cartproducts][populate]': 'product',
    }
    response = requests.get(
        f'{strapi_url}/api/carts',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=cart_filter
    )
    response.raise_for_status()
    return response.json()


def create_cart(telegram_id, strapi_url, strapi_token):
    cart_payload = {
        'data': {
            'telegram_id': telegram_id
        },
    }
    response = requests.post(
        f'{strapi_url}/api/carts',
        headers={
            'Authorization': f'bearer {strapi_token}'
        },
        json=cart_payload
    )
    response.raise_for_status()
    return response.status_code


def delete_cart_product(product_id, strapi_url, strapi_token):
    response = requests.delete(
        f'{strapi_url}/api/product-in-carts/{product_id}',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        }
    )
    response.raise_for_status()
    return response.status_code


def get_product_and_picture(product_id, strapi_url, strapi_token):
    payload = {
        'populate': 'image'
    }

    response = requests.get(
        f'{strapi_url}/api/products/{product_id}',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=payload
    )
    response.raise_for_status()
    return response.json()


def get_user(cart_id, strapi_url, strapi_token):
    user_filter = {'filters[cart][$eq]': cart_id}
    response = requests.get(
        f'{strapi_url}/api/users',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        params=user_filter,
    )
    response.raise_for_status()
    return response.json()


def save_email(user_id, email, strapi_url, strapi_token):
    payload = {'email': email}
    response = requests.put(
        f'{strapi_url}/api/users/{user_id}',
        headers={
            'Authorization': f'Bearer {strapi_token}'
        },
        json=payload
    )
    response.raise_for_status()
    return response.status_code


def get_product_image(strapi_url, image_link):
    image_link = f'{strapi_url}{image_link}'
    response = requests.get(image_link)
    response.raise_for_status()
    return BytesIO(response.content)
