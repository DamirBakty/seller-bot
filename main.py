from environs import Env
import requests


def main():
    env = Env()
    env.read_env()
    access_token = env.str('STRAPI_ACCESS_TOKEN')
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get('http://localhost:1337/api/products', headers=headers)
    products = r.json()
    print(products)


if __name__ == '__main__':
    main()


