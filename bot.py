import telebot
from telebot import types
from datetime import datetime
import requests
import random
from database import (add_user, get_user, get_user_by_username,
                      get_all_users, delete_user, add_friend, update_user)

# ключи
Token_tg = '7148550227:AAFE_eBe-UkNE42UebmujyvidyAipQe8Zwg'
Api = 'be1feead-ce5e-4c74-b620-7b32364dc431'
bot = telebot.TeleBot(Token_tg)

users = {}

# Вопросы и варианты ответов для предпочтений (для команды /recommend)
Questions = {
    "price": {
        "question": "Какой уровень цен вас интересует?",
        "options": ["💰 Бюджетный", "💵 Средний", "💎 Премиум"]
    },
    "atmosphere": {
        "question": "Какая атмосфера предпочтительна?",
        "options": ["😌 Спокойная", "🎉 Веселая", "💼 Деловая"]
    },
    "crowd": {
        "question": "Какое количество людей предпочитаете?",
        "options": ["👥 Многолюдно", "👫 Умеренно", "🚶‍♂️ Мало людей"]
    },
    "music": {
        "question": "Какая музыка предпочтительна?",
        "options": ["🎵 Любая", "🎶 Живая", "🔇 Без музыки"]
    },
    "food": {
        "question": "Какое питание предпочитаете?",
        "options": ["🍔 Фастфуд", "🍽️ Ресторанное", "🥗 Здоровое"]
    },
    "alcohol": {
        "question": "Отношение к алкоголю?",
        "options": ["🍻 Есть алкоголь", "🚫 Только безалкогольное", "🤷 Не важно"]
    },
    "outdoor": {
        "question": "Предпочтение по расположению?",
        "options": ["🌳 На открытом воздухе", "🏢 В помещении", "🤷 Не важно"]
    },
    "accessibility": {
        "question": "Важна ли доступность для маломобильных?",
        "options": ["♿ Да, важно", "🚶‍♂️ Нет, не важно"]
    },
    "parking": {
        "question": "Нужна ли парковка?",
        "options": ["🅿️ Да, нужна", "🚶‍♂️ Нет, не нужна"]
    },
    "wifi": {
        "question": "Нужен ли Wi-Fi?",
        "options": ["📶 Да, нужен", "🚫 Нет, не нужен"]
    }
}


def register_user(user_id, username):
    existing_user = get_user_by_username(username)
    if existing_user:
        return False

    try:
        add_user(user_id, username)
        users[user_id] = {
            'username': username,
            'favorites': [],
            'reviews': {},
            'friends': [],
            'friend_requests': [],
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True
    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        return False


def get_user_profile(user_id):
    user = get_user(user_id)
    if user:
        user_data = {
            'user_id': user[0],
            'username': user[1],
            'favorites': user[2].split(',') if user[2] else [],
            'reviews': eval(user[3]) if user[3] else {},
            'friends': [int(friend_id) for friend_id in user[4].split(',') if friend_id] if user[4] else [],
            'friend_requests': [int(req_id) for req_id in user[5].split(',') if req_id] if user[5] else [],
            'registration_date': user[6]
        }

        friends_usernames = []
        for friend_id in user_data['friends']:
            friend = users.get(friend_id)
            if friend:
                friends_usernames.append(friend['username'])

        favorites = ', '.join(user_data['favorites']) or 'Нет избранных мест'
        reviews = '\n'.join([f"{addr}: {review}" for addr, review in user_data['reviews'].items()]) or 'Нет отзывов'
        friends_count = len(friends_usernames)
        friends_list = ', '.join(friends_usernames) or 'Нет друзей'

        return (f"👤 Профиль пользователя:\n"
                f"Имя: {user_data['username']}\n"
                f"🏠 Избранные места: {favorites}\n"
                f"📝 Отзывы:\n{reviews}\n"
                f"👥 Друзья: {friends_list}\n"
                f"📅 Дата регистрации: {user_data['registration_date']}")
    return "Пользователь не найден."


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать в МирУголков! Отправьте команду /register для регистрации.")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/register - Зарегистрироваться в системе\n"
        "/add_favorite - Добавить место в избранное\n"
        "/remove_favorite - Удалить место из избранного\n"
        "/add_review - Добавить отзыв о месте\n"
        "/remove_review - Удалить отзыв\n"
        "/find_friend - Найти друга по имени\n"
        "/profile - Показать свой профиль\n"
        "/delete_profile - Удалить свой профиль\n"
        "/change_username - Изменить имя пользователя\n"
        "/view_friends - Просмотреть список друзей\n"
        "/remove_friend - Удалить друга\n"
        "/view_requests - Просмотреть входящие запросы в друзья\n"
        "/search - Поиск мест по городу и запросу\n"
        "/recommend - Персонализированные рекомендации мест"
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['register'])
def register(message):
    user_id = message.from_user.id
    if user_id in users:
        bot.send_message(message.chat.id,
                         "Вы уже зарегистрированы! Используйте команду /profile для просмотра своего профиля.")
    else:
        bot.send_message(message.chat.id, "Введите ваше имя:")
        bot.register_next_step_handler(message, process_registration)


def process_registration(message):
    username = message.text.strip()
    if register_user(message.from_user.id, username):
        bot.send_message(message.chat.id, "Вы успешно зарегистрированы!")
    else:
        bot.send_message(message.chat.id, "Это имя уже занято. Пожалуйста, выберите другое имя.")
        bot.register_next_step_handler(message, process_registration)


@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = message.from_user.id
    profile_info = get_user_profile(user_id)
    bot.send_message(message.chat.id, profile_info)

@bot.message_handler(commands=['add_favorite'])
def add_favorite_place(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    bot.send_message(user_id, "Введите адрес места для добавления в избранное:")
    bot.register_next_step_handler(message, process_add_favorite)


def process_add_favorite(message):
    user_id = message.from_user.id
    address = message.text.strip()
    users[user_id]['favorites'].append(address)
    update_user(user_id, users[user_id])
    bot.send_message(user_id, f"Адрес '{address}' добавлен в избранные места!")


@bot.message_handler(commands=['remove_favorite'])
def remove_favorite_place(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return

    favorites = users[user_id]['favorites']
    if not favorites:
        bot.send_message(user_id, "У вас нет избранных мест для удаления.")
        return

    favorites_list = "\n".join([f"{i + 1}. {fav}" for i, fav in enumerate(favorites)])
    bot.send_message(user_id, f"Ваши избранные места:\n{favorites_list}\nВведите номер места для удаления:")
    bot.register_next_step_handler(message, process_remove_favorite)


def process_remove_favorite(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(users[user_id]['favorites']):
            removed_place = users[user_id]['favorites'].pop(index)
            update_user(user_id, users[user_id])
            bot.send_message(user_id, f"Место '{removed_place}' удалено из избранного!")
        else:
            bot.send_message(user_id, "Пожалуйста, попробуйте снова.")
            bot.register_next_step_handler(message, process_remove_favorite)
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите номер места.")
        bot.register_next_step_handler(message, process_remove_favorite)


@bot.message_handler(commands=['delete_profile'])
def delete_profile_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    bot.send_message(user_id, "Вы уверены, что хотите удалить свой профиль? (да/нет)")
    bot.register_next_step_handler(message, process_delete_profile)


def process_delete_profile(message):
    user_id = message.from_user.id
    response = message.text.strip().lower()
    if response == 'да':
        delete_user(user_id)
        del users[user_id]
        bot.send_message(user_id, "Ваш профиль был удален.")
    else:
        bot.send_message(user_id, "Удаление профиля отменено.")


@bot.message_handler(commands=['add_review'])
def add_review_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    bot.send_message(user_id, "Введите адрес места:")
    bot.register_next_step_handler(message, process_review_address)


def process_review_address(message):
    user_id = message.from_user.id
    address = message.text.strip()
    bot.send_message(user_id, "Введите описание места:")
    bot.register_next_step_handler(message, lambda msg: process_review_description(msg, address))


def process_review_description(message, address):
    user_id = message.from_user.id
    description = message.text.strip()
    users[user_id]['reviews'][address] = description
    update_user(user_id, users[user_id])
    bot.send_message(user_id, f"Отзыв на адрес '{address}' добавлен!")


@bot.message_handler(commands=['remove_review'])
def remove_review_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return

    reviews = users[user_id]['reviews']
    if not reviews:
        bot.send_message(user_id, "У вас нет отзывов для удаления.")
        return

    reviews_list = "\n".join([f"{i + 1}. {addr}" for i, addr in enumerate(reviews.keys())])
    bot.send_message(user_id, f"Ваши отзывы:\n{reviews_list}\nВведите номер отзыва для удаления:")
    bot.register_next_step_handler(message, process_remove_review)


def process_remove_review(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.strip()) - 1
        addresses = list(users[user_id]['reviews'].keys())
        if 0 <= index < len(addresses):
            removed_address = addresses[index]
            removed_review = users[user_id]['reviews'].pop(removed_address)
            update_user(user_id, users[user_id])
            bot.send_message(user_id, f"Отзыв на адрес '{removed_address}' удален!")
        else:
            bot.send_message(user_id, "Пожалуйста, попробуйте снова.")
            bot.register_next_step_handler(message, process_remove_review)
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите номер отзыва.")
        bot.register_next_step_handler(message, process_remove_review)


@bot.message_handler(commands=['find_friend'])
def find_friend_by_name(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    bot.send_message(user_id, "Введите имя друга для поиска:")
    bot.register_next_step_handler(message, process_find_friend)


def process_find_friend(message):
    friend_name = message.text.strip()
    found_friends = []

    for user_id, user_data in users.items():
        if (user_data['username'].lower() == friend_name.lower() and
                user_id != message.from_user.id and
                user_id not in users[message.from_user.id]['friends']):
            found_friends.append((user_id, user_data['username']))

    if found_friends:
        markup = types.InlineKeyboardMarkup()
        for friend_id, friend_username in found_friends:
            markup.add(types.InlineKeyboardButton(
                f"Отправить запрос {friend_username}",
                callback_data=f'send_request_{friend_id}'
            ))
        bot.send_message(message.chat.id, "Найденные пользователи:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Пользователи не найдены или уже являются вашими друзьями.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('send_request_'))
def handle_send_request(call):
    friend_id = int(call.data.split('_')[2])
    user_id = call.from_user.id

    if friend_id not in users:
        bot.answer_callback_query(call.id, "Пользователь не найден.")
        return

    if friend_id in users[user_id]['friends']:
        bot.answer_callback_query(call.id, "Вы уже друзья с этим пользователем.")
        return

    if user_id in users[friend_id]['friend_requests']:
        bot.answer_callback_query(call.id, "Вы уже отправили запрос этому пользователю.")
        return

    users[friend_id]['friend_requests'].append(user_id)
    update_user(friend_id, users[friend_id])

    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("✅ Принять", callback_data=f'accept_{user_id}')
    reject_button = types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{user_id}')
    markup.add(accept_button, reject_button)

    bot.send_message(
        friend_id,
        f"📩 {users[user_id]['username']} отправил вам запрос на дружбу!",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, f"Запрос на дружбу отправлен {users[friend_id]['username']}.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def accept_friend_request(call):
    requester_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    if requester_id not in users[user_id]['friend_requests']:
        bot.answer_callback_query(call.id, "Запрос не найден.")
        return

    if requester_id not in users[user_id]['friends']:
        users[user_id]['friends'].append(requester_id)
    if user_id not in users[requester_id]['friends']:
        users[requester_id]['friends'].append(user_id)

    users[user_id]['friend_requests'].remove(requester_id)

    update_user(user_id, users[user_id])
    update_user(requester_id, users[requester_id])

    bot.edit_message_text(
        f"✅ Вы приняли запрос от {users[requester_id]['username']}, теперь вы друзья!",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    bot.send_message(
        requester_id,
        f"🎉 {users[user_id]['username']} принял вашу заявку в друзья!"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_friend_request(call):
    requester_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    if requester_id not in users[user_id]['friend_requests']:
        bot.answer_callback_query(call.id, "Запрос не найден.")
        return

    users[user_id]['friend_requests'].remove(requester_id)
    update_user(user_id, users[user_id])

    bot.edit_message_text(
        f"❌ Вы отклонили запрос от {users[requester_id]['username']}.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    bot.send_message(
        requester_id,
        f"😞 {users[user_id]['username']} отклонил вашу заявку в друзья."
    )


@bot.message_handler(commands=['view_friends'])
def view_friends_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return

    friends_list = []
    for friend_id in users[user_id]['friends']:
        friend = users.get(friend_id)
        if friend:
            friends_list.append(friend['username'])

    if friends_list:
        bot.send_message(user_id, "Ваши друзья:\n" + "\n".join(friends_list))
    else:
        bot.send_message(user_id, "У вас пока нет друзей.")


@bot.message_handler(commands=['view_requests'])
def view_friend_requests(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return

    requests_list = []
    for req_id in users[user_id]['friend_requests']:
        requester = users.get(req_id)
        if requester:
            requests_list.append(requester['username'])

    if requests_list:
        markup = types.InlineKeyboardMarkup()
        for req_id in users[user_id]['friend_requests']:
            requester = users.get(req_id)
            if requester:
                markup.add(
                    types.InlineKeyboardButton(
                        f"Принять запрос от {requester['username']}",
                        callback_data=f'accept_{req_id}'
                    ),
                    types.InlineKeyboardButton(
                        f"Отклонить запрос от {requester['username']}",
                        callback_data=f'reject_{req_id}'
                    )
                )
        bot.send_message(user_id, "Входящие запросы в друзья:", reply_markup=markup)
    else:
        bot.send_message(user_id, "У вас нет входящих запросов в друзья.")


@bot.message_handler(commands=['remove_friend'])
def remove_friend_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return

    friends_list = []
    for friend_id in users[user_id]['friends']:
        friend = users.get(friend_id)
        if friend:
            friends_list.append(f"{len(friends_list) + 1}. {friend['username']}")

    if not friends_list:
        bot.send_message(user_id, "У вас нет друзей для удаления.")
        return

    bot.send_message(
        user_id,
        f"Ваши друзья:\n" + "\n".join(friends_list) + "\n\nВведите номер друга, которого хотите удалить:"
    )
    bot.register_next_step_handler(message, process_remove_friend)


def process_remove_friend(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.strip()) - 1
        friends_ids = users[user_id]['friends']
        if 0 <= index < len(friends_ids):
            friend_id = friends_ids[index]
            friend = users.get(friend_id)

            users[user_id]['friends'].remove(friend_id)
            if user_id in users[friend_id]['friends']:
                users[friend_id]['friends'].remove(user_id)

            update_user(user_id, users[user_id])
            update_user(friend_id, users[friend_id])

            bot.send_message(
                user_id,
                f"Вы больше не друзья с {friend['username']}."
            )
            bot.send_message(
                friend_id,
                f"{users[user_id]['username']} удалил вас из друзей."
            )
        else:
            bot.send_message(user_id, "Неверный номер. Пожалуйста, попробуйте снова.")
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите номер друга.")


@bot.message_handler(commands=['change_username'])
def change_username_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    bot.send_message(user_id, "Введите новое имя пользователя:")
    bot.register_next_step_handler(message, process_change_username)


def process_change_username(message):
    user_id = message.from_user.id
    new_username = message.text.strip()

    existing_user = get_user_by_username(new_username)
    if existing_user and existing_user['user_id'] != user_id:
        bot.send_message(user_id, "Это имя уже занято. Пожалуйста, выберите другое имя.")
        bot.register_next_step_handler(message, process_change_username)
    else:
        users[user_id]['username'] = new_username
        update_user(user_id, users[user_id])
        bot.send_message(user_id, f"Ваше имя пользователя изменено на {new_username}.")


@bot.message_handler(commands=['search'])
def search_command(message):
    bot.send_message(message.chat.id, "Привет! В каком городе искать места?")
    bot.register_next_step_handler(message, process_search_city)


def process_search_city(message):
    city = message.text.strip()
    if not city:
        bot.send_message(message.chat.id, "Пожалуйста, введите название города.")
        bot.register_next_step_handler(message, process_search_city)
        return

    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {'search_data': {}}
    users[user_id]['search_data'] = {'city': city}

    bot.send_message(message.chat.id, f"Ищем в городе {city}. Что ищем? (Например: кафе, парк, музей)")
    bot.register_next_step_handler(message, process_search_query)


def process_search_query(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "Пожалуйста, введите что искать.")
        bot.register_next_step_handler(message, process_search_query)
        return

    user_id = message.from_user.id
    city = users[user_id]['search_data']['city']

    places = yandex_geocode(city, query)
    if not places:
        bot.send_message(message.chat.id, "Ничего не найдено. Попробуйте другой запрос или уточните параметры поиска.")
        return

    message_text = "🔍 Найденные места:\n\n"
    for i, place in enumerate(places, 1):
        message_text += (
            f"{i}. <b>{place['name']}</b>\n"
            f"📍 Адрес: {place['address']}\n"
            f"🌐 Координаты: {place['lat']}, {place['lon']}\n\n"
        )

    markup = types.InlineKeyboardMarkup()
    refresh_button = types.InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_search_{city}_{query}")
    markup.add(refresh_button)

    bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('refresh_search_'))
def refresh_search_results(call):
    data = call.data.split('_')
    city = data[2]
    query = '_'.join(data[3:])

    places = yandex_geocode(city, query)
    if not places:
        bot.answer_callback_query(call.id, "Ничего не найдено. Попробуйте другой запрос.")
        return

    message_text = "🔍 Найденные места:\n\n"
    for i, place in enumerate(places, 1):
        message_text += (
            f"{i}. <b>{place['name']}</b>\n"
            f"📍 Адрес: {place['address']}\n"
            f"🌐 Координаты: {place['lat']}, {place['lon']}\n\n"
        )

    markup = types.InlineKeyboardMarkup()
    refresh_button = types.InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_search_{city}_{query}")
    markup.add(refresh_button)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=message_text,
        reply_markup=markup,
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id, "Результаты обновлены")


def yandex_geocode(city, query):
    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": Api,
            "geocode": f"{city}, {query}",
            "format": "json",
            "results": 5,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        places = []
        features = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])

        if not features:
            return None

        for feature in features:
            geo = feature.get("GeoObject", {})
            name = geo.get("name", "Название не указано")
            address = geo.get("description", "Адрес не указан")
            coords = geo.get("Point", {}).get("pos", "").split()

            if len(coords) >= 2:
                places.append({
                    "name": name,
                    "address": address,
                    "lat": coords[1],
                    "lon": coords[0],
                })

        return places if places else None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к API Яндекс: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None


@bot.message_handler(commands=['recommend'])
def recommend_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "⚠️ Сначала зарегистрируйтесь с помощью команды /register.")
        return

    users[user_id]['recommend_data'] = {}
    bot.send_message(user_id,
                     "💡  В каком городе будем искать?")
    bot.register_next_step_handler(message, recommend_ask_city)


def recommend_ask_city(message):
    user_id = message.from_user.id
    city = message.text.strip()
    if not city:
        bot.send_message(user_id, "⚠️ Пожалуйста, введите название города.")
        bot.register_next_step_handler(message, recommend_ask_city)
        return

    users[user_id]['recommend_data']['city'] = city
    bot.send_message(
        user_id,
        f"🌆 Какое место вас интересует? (Например: кафе, парк, музей, ресторан)")
    bot.register_next_step_handler(message, recommend_ask_query)


def recommend_ask_query(message):
    user_id = message.from_user.id
    query = message.text.strip()
    if not query:
        bot.send_message(user_id, "⚠️ Пожалуйста, укажите, что ищем.")
        bot.register_next_step_handler(message, recommend_ask_query)
        return

    users[user_id]['recommend_data']['query'] = query
    users[user_id]['recommend_data']['preferences'] = {}

    selected_questions = random.sample(list(Questions.items()), 3)
    users[user_id]['recommend_data']['selected_questions'] = [q[0] for q in selected_questions]
    users[user_id]['recommend_data']['current_question'] = 0

    recommend_ask_next_question(message)


def recommend_ask_next_question(message):
    user_id = message.from_user.id
    recommend_data = users[user_id]['recommend_data']
    questions = recommend_data['selected_questions']
    current = recommend_data['current_question']

    if current >= len(questions):
        recommend_find_places(message)
        return

    question_key = questions[current]
    question_data = Questions[question_key]

    markup = types.InlineKeyboardMarkup()
    for option in question_data["options"]:
        markup.add(types.InlineKeyboardButton(option, callback_data=f"pref_{question_key}_{option}"))

    bot.send_message(
        user_id,
        text=question_data["question"],
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('pref_'))
def handle_preference(call):
    user_id = call.from_user.id
    _, question_key, option = call.data.split('_', 2)

    users[user_id]['recommend_data']['preferences'][question_key] = option
    users[user_id]['recommend_data']['current_question'] += 1

    message = types.Message.de_json(call.message.json)
    message.from_user = call.from_user
    recommend_ask_next_question(message)


def recommend_find_places(message):
    user_id = message.from_user.id
    recommend_data = users[user_id]['recommend_data']
    city = recommend_data.get("city", "")
    query = recommend_data.get("query", "")
    preferences = recommend_data.get("preferences", {})

    if not city or not query:
        bot.send_message(user_id, "⚠️ Недостаточно данных для поиска. Начните заново.")
        return recommend_command(message)

    search_query = f"{query}"

    places = yandex_geocode(city, search_query)  # Используем существующую функцию yandex_geocode

    if not places:
        bot.send_message(
            user_id,
            "😔 Ничего не найдено по вашим критериям. Попробуйте изменить параметры поиска.")
        return recommend_command(message)

    recommend_send_results(user_id, places)


def recommend_send_results(user_id, places):
    message = "💡 *Найденные места по вашим предпочтениям:*\n\n"
    for i, place in enumerate(places, 1):
        message += (
            f"{i}. *{place['name']}*\n"
            f"📍 Адрес: {place['address']}\n"
            f"🌐 Координаты: {place['lat']}, {place['lon']}\n\n"
        )

    # Создаем кнопки для интерактивного меню
    markup = types.InlineKeyboardMarkup()

    bot.send_message(
        user_id,
        text=message,
        reply_markup=markup,
        parse_mode="Markdown"
    )


if __name__ == "__main__":
    all_users_from_db = get_all_users()
    for db_user in all_users_from_db:
        users[db_user['user_id']] = {
            'username': db_user['username'],
            'favorites': db_user['favorites'],
            'reviews': db_user['reviews'],
            'friends': [int(friend_id) for friend_id in db_user['friends'] if friend_id],
            'friend_requests': [int(req_id) for req_id in db_user['friend_requests'] if req_id],
            'registration_date': db_user['registration_date']
        }
    bot.polling(none_stop=True)