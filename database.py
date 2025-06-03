import sqlite3

# Создание таблицы
def create_tables():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Добавление нового пользователя
def add_user(telegram_id, full_name, phone, email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (telegram_id, full_name, phone, email) VALUES (?, ?, ?, ?)",
            (telegram_id, full_name, phone, email)
        )
    conn.commit()
    conn.close()

# Обновление баллов
def update_score(telegram_id, score):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = ? WHERE telegram_id = ?", (score, telegram_id))
    conn.commit()
    conn.close()

# Получение баллов пользователя
def get_score(telegram_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Топ-5 пользователей
def get_top_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, score FROM users ORDER BY score DESC LIMIT 5")
    result = cursor.fetchall()
    conn.close()
    return result

# Получение всех пользователей для экспорта
def get_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone, email, score FROM users")
    result = cursor.fetchall()
    conn.close()
    return result
