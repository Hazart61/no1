import telebot
from telebot import types
from datetime import datetime
import requests
from database import (add_user, get_user, get_user_by_username,
                      get_all_users, delete_user, add_friend, update_user)

# ключи
TOKEN = '7148550227:AAFE_eBe-UkNE42UebmujyvidyAipQe8Zwg'
YANDEX_API_KEY = 'ee7ac1b0-0384-4666-8561-c20f38523b9a'
bot = telebot.TeleBot(TOKEN)

users = {}

def register_user(user_id, username):
    existing_user = get_user_by_username(username)
    if existing_user:
        return False  # Имя занято

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

# Функция для получения профиля пользователя
def get_user_profile(user_id):
    user = get_user(user_id)
    if user:
        user_data = {
            'user_id': user[0],
            'username': user[1],
            'favorites': user[2].split(',') if user[2] else [],
            'reviews': eval(user[3]) if user[3] else {},
            'friends': user[4].split(',') if user[4] else [],
            'friend_requests': user[5].split(',') if user[5] else [],
            'registration_date': user[6]
        }
        favorites = ', '.join(user_data['favorites']) or 'Нет избранных мест'
        reviews = '\n'.join([f"{addr}: {review}" for addr, review in user_data['reviews'].items()]) or 'Нет отзывов'
        friends_count = len(user_data['friends'])
        return (f"👤 Профиль пользователя:\n"
                f"Имя: {user_data['username']}\n"
                f"🏠 Избранные места: {favorites}\n"
                f"📝 Отзывы:\n{reviews}\n"
                f"👥 Количество друзей: {friends_count}\n"
                f"📅 Дата регистрации: {user_data['registration_date']}")
    return "Пользователь не найден."

# Функция для поиска мест через API
def search_places(city, query):
    url = 'https://search-maps.yandex.ru/v1/'
    params = {
        'apikey': YANDEX_API_KEY,
        'text': f'{query}, {city}',
        'lang': 'ru_RU',
        'results': 10,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        places = []
        for feature in data.get('features', []):
            place_name = feature['properties']['name']
            address = feature['properties']['description']
            coordinates = feature['geometry']['coordinates']
            places.append({
                'name': place_name,
                'address': address,
                'coordinates': coordinates,
            })
        return places
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return []
    except Exception as err:
        print(f"Other error occurred: {err}")
        return []

# Функция для обработки результатов поиска мест
def send_places_list(chat_id, places):
    markup = types.InlineKeyboardMarkup()
    for i in range(min(5, len(places))):
        place = places[i]
        markup.add(types.InlineKeyboardButton(f"{place['name']} - {place['address']}", url=f"https://yandex.ru/maps/?text={place['coordinates'][1]},{place['coordinates'][0]}"))
    if len(places) > 5:
        markup.add(types.InlineKeyboardButton("Далее", callback_data='next_page'))
    bot.send_message(chat_id, "Результаты поиска:", reply_markup=markup)

# Функция для подбора мест по критериям
def recommend_places(user_id):
    questions = [
        "Какой тип места вы предпочитаете? (например, кафе, парк, музей)",
        "Какой бюджет вы планируете? (например, бюджетный, средний, высокий)",
        "Какое время года вы предпочитаете? (например, лето, зима, весна, осень)",
        "Какое время суток вы предпочитаете? (например, утро, день, вечер, ночь)",
        "Какие особенности вы ищете? (например, семейное место, романтическое место, место для активного отдыха)"
    ]
    answers = []

    def ask_question(question_index):
        if question_index < len(questions):
            bot.send_message(user_id, questions[question_index])
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: process_answer(msg, question_index))
        else:
            # Подбор мест по ответам
            places = search_places(" ", " ".join(answers))
            send_places_list(user_id, places)

    def process_answer(message, question_index):
        answers.append(message.text.strip())
        ask_question(question_index + 1)

    ask_question(0)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать в МирУголков! Отправьте команду /register для регистрации.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/register - Зарегистрироваться в системе\n"
        "/search - Найти места\n"
        "/add_favorite - Добавить место в избранное\n"
        "/remove_favorite - Удалить место из избранного\n"
        "/add_review - Добавить отзыв о месте\n"
        "/remove_review - Удалить отзыв\n"
        "/find_friend - Найти друга по имени\n"
        "/profile - Показать свой профиль\n"
        "/recommend - Получить рекомендации по местам для отдыха\n"
        "/delete_profile - Удалить свой профиль\n"
        "/change_username - Изменить имя пользователя\n"
        "/view_friends - Просмотреть список друзей\n"
        "/remove_friend - Удалить друга\n"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['register'])
def register(message):
    user_id = message.from_user.id
    if user_id in users:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы! Используйте команду /profile для просмотра своего профиля."
                                          "\nВведите /help что б посмотреть доступные команды")
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

@bot.message_handler(commands=['search'])
def handle_search(message):
    bot.send_message(message.chat.id, "Введите название города:")
    bot.register_next_step_handler(message, process_city)

def process_city(message):
    city = message.text.strip()
    bot.send_message(message.chat.id, "Введите слово для поиска:")
    bot.register_next_step_handler(message, lambda msg: process_search(msg, city))

def process_search(message, city):
    query = message.text.strip()
    places = search_places(city, query)
    if not places:
        bot.send_message(message.chat.id, "Ничего не найдено.")
        return
    send_places_list(message.chat.id, places)

@bot.callback_query_handler(func=lambda call: call.data == 'next_page')
def next_page(call):
    bot.send_message(call.message.chat.id, "Здесь будут следующие результаты.")

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

@bot.message_handler(commands=['recommend'])
def recommend_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    recommend_places(user_id)

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
    found_friends = [user for user in users.values() if user['username'] == friend_name]
    if found_friends:
        friend_list = "\n".join([f"{friend['username']}" for friend in found_friends])
        markup = types.InlineKeyboardMarkup()
        for friend in found_friends:
            markup.add(types.InlineKeyboardButton(f"Отправить запрос {friend['username']}",
                                                  callback_data=f'send_request_{friend["username"]}'))
        bot.send_message(message.chat.id, f"Найденные друзья:\n{friend_list}", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Друзья не найдены.")

@bot.message_handler(commands=['remove_friend'])
def remove_friend(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    friends_list = ', '.join(users[user_id]['friends']) or 'Нет друзей.'
    bot.send_message(user_id, f"Ваши друзья: {friends_list}\nВведите имя друга для удаления:")
    bot.register_next_step_handler(message, process_remove_friend)

def process_remove_friend(message):
    user_name_to_remove = message.text.strip()
    user_found = next((user for user in users.values() if user['username'] == user_name_to_remove), None)
    if user_found and user_found['user_id'] in users[message.from_user.id]['friends']:
        users[message.from_user.id]['friends'].remove(user_found['user_id'])
        update_user(message.from_user.id, users[message.from_user.id])
        bot.send_message(message.chat.id, f"{user_name_to_remove} был удален из ваших друзей.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('send_request_'))
def handle_send_request(call):
    friend_username = call.data.split('_')[2]
    user_id = call.message.chat.id
    if send_friend_request(user_id, friend_username):
        bot.answer_callback_query(call.id, f"Запрос на дружбу отправлен {friend_username}.")
    else:
        bot.answer_callback_query(call.id, "Не удалось отправить запрос.")

def view_friends(user_id, friend_id):
    return friend_id in users[user_id]['friends']

def send_friend_request(from_user_id, to_username):
    to_user = next((user for user in users.values() if user['username'] == to_username), None)

    if to_user:
        to_user_id = to_user['user_id']

        # Проверяем, являются ли пользователи друзьями
        if view_friends(from_user_id, to_user_id):
            bot.send_message(from_user_id, "❌ Вы уже друзья с этим пользователем.")
            return False

        # Проверяем, был ли уже отправлен запрос
        if from_user_id not in to_user['friend_requests']:
            users[to_user_id]['friend_requests'].append(from_user_id)
            update_user(to_user_id, users[to_user_id])

            # Создаем клавиатуру с кнопками "Принять" и "Отклонить"
            markup = types.InlineKeyboardMarkup()
            accept_button = types.InlineKeyboardButton("✅ Принять", callback_data=f'accept_{from_user_id}')
            reject_button = types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{from_user_id}')
            markup.add(accept_button, reject_button)

            bot.send_message(
                to_user_id,
                f"📩 {users[from_user_id]['username']} отправил вам запрос на дружбу!",
                reply_markup=markup
            )
            return True

    return False

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def accept_friend_request(call):
    requester_id = int(call.data.split('_')[1])
    user_id = call.message.chat.id

    if requester_id in users[user_id]['friend_requests']:
        users[user_id]['friends'].append(requester_id)
        users[requester_id]['friends'].append(user_id)

        # Удаляем запрос из списка запросов на дружбу
        users[user_id]['friend_requests'].remove(requester_id)

        update_user(user_id, users[user_id])
        update_user(requester_id, users[requester_id])

        bot.edit_message_text(
            f"✅ Вы приняли запрос от {users[requester_id]['username']}, теперь вы друзья!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        bot.send_message(requester_id, f"🎉 {users[user_id]['username']} принял вашу заявку в друзья!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_friend_request(call):
    requester_id = int(call.data.split('_')[1])
    user_id = call.message.chat.id

    if requester_id in users[user_id]['friend_requests']:
        users[user_id]['friend_requests'].remove(requester_id)

        update_user(user_id, users[user_id])

        bot.edit_message_text(
            f"❌ Вы отклонили запрос от {users[requester_id]['username']}.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        bot.send_message(requester_id, f"😞 {users[user_id]['username']} отклонил вашу заявку в друзья.")

@bot.message_handler(commands=['view_friends'])
def view_friends_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /register.")
        return
    friends_list = ', '.join(users[user_id]['friends']) or 'Нет друзей.'
    bot.send_message(user_id, f"Ваши друзья: {friends_list}")

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
    if get_user_by_username(new_username):
        bot.send_message(user_id, "Это имя уже занято. Пожалуйста, выберите другое имя.")
        bot.register_next_step_handler(message, process_change_username)
    else:
        users[user_id]['username'] = new_username
        update_user(user_id, users[user_id])
        bot.send_message(user_id, f"Ваше имя пользователя изменено на {new_username}.")

if __name__ == "__main__":
    all_users_from_db = get_all_users()
    for db_user in all_users_from_db:
        users[db_user['user_id']] = db_user
    bot.polling(none_stop=True)