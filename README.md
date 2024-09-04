# БОТ для продажи в телеграме

Бот использует api STAPI в качестве базы данных для хранения информации о товарах и заказах.

## Как запустить

* Скачайте код
* Перейдите в корневую папку проекта
* Создайте виртуальное окружение
* Установите зависимости

```bash
$ pip install -r requirements.txt
```

## Установка Redis

[Установите и запустите Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/), если этого
ещё не сделали.

* Создайте .env файл и скопируйте содержимое из .env.example
* Поменяйте данные под свой проект
* * STRAPI_ACCESS_TOKEN - токен авторизации для strapi
* * TG_BOT_TOKEN - Токен телеграм бота
* * DATABASE_HOST - хост на котором поднят Redis
* * DATABASE_PORT - порт Redis
* * STRAPI_URL - Адрес веб сервера strapi

* Запустите бота для Telegram

```bash
$ python tg_bot.py
```
