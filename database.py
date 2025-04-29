import sqlite3
from datetime import datetime

def get_connection():
    return sqlite3.connect('users.db')

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        favorites TEXT,
        reviews TEXT,
        friends TEXT,
        friend_requests TEXT,
        registration_date TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (user_id, username, favorites, reviews, friends, friend_requests, registration_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, '', '', '', '', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'favorites': user[2].split(',') if user[2] else [],
            'reviews': eval(user[3]) if user[3] else {},
            'friends': user[4].split(',') if user[4] else [],
            'friend_requests': user[5].split(',') if user[5] else [],
            'registration_date': user[6]
        }
    return None

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return [
        {
            'user_id': user[0],
            'username': user[1],
            'favorites': user[2].split(',') if user[2] else [],
            'reviews': eval(user[3]) if user[3] else {},
            'friends': user[4].split(',') if user[4] else [],
            'friend_requests': user[5].split(',') if user[5] else [],
            'registration_date': user[6]
        }
        for user in users
    ]

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def are_friends(user_id_1, user_id_2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_1,))
    friends_list_1 = cursor.fetchone()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_2,))
    friends_list_2 = cursor.fetchone()
    conn.close()

    if friends_list_1 and friends_list_2:
        friends_list_1 = friends_list_1[0].split(',') if friends_list_1[0] else []
        friends_list_2 = friends_list_2[0].split(',') if friends_list_2[0] else []

        return str(user_id_2) in friends_list_1 and str(user_id_1) in friends_list_2

    return False

def add_friend(user_id_1, user_id_2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_1,))
    friends_list_1 = cursor.fetchone()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_2,))
    friends_list_2 = cursor.fetchone()

    if friends_list_1 and friends_list_2:
        friends_list_1 = friends_list_1[0].split(',') if friends_list_1[0] else []
        friends_list_2 = friends_list_2[0].split(',') if friends_list_2[0] else []

        friends_list_1.append(str(user_id_2))
        friends_list_2.append(str(user_id_1))

        cursor.execute('UPDATE users SET friends = ? WHERE user_id = ?', (','.join(friends_list_1), user_id_1))
        cursor.execute('UPDATE users SET friends = ? WHERE user_id = ?', (','.join(friends_list_2), user_id_2))

        conn.commit()
    conn.close()

def remove_friend(user_id_1, user_id_2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_1,))
    friends_list_1 = cursor.fetchone()
    cursor.execute('SELECT friends FROM users WHERE user_id = ?', (user_id_2,))
    friends_list_2 = cursor.fetchone()

    if friends_list_1 and friends_list_2:
        friends_list_1 = [f for f in friends_list_1[0].split(',') if f != str(user_id_2)]
        friends_list_2 = [f for f in friends_list_2[0].split(',') if f != str(user_id_1)]

        cursor.execute('UPDATE users SET friends = ? WHERE user_id = ?', (','.join(friends_list_1), user_id_1))
        cursor.execute('UPDATE users SET friends = ? WHERE user_id = ?', (','.join(friends_list_2), user_id_2))

        conn.commit()
    conn.close()

def update_user(user_id, user_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET username = ?, favorites = ?, friends = ?, reviews = ?, friend_requests = ?
        WHERE user_id = ?
    ''', (
        user_data['username'],
        ','.join(user_data['favorites']),
        ','.join(map(str, user_data['friends'])),
        str(user_data['reviews']),
        ','.join(map(str, user_data['friend_requests'])),
        user_id
    ))
    conn.commit()
    conn.close()

create_table()