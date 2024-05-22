import sqlite3

def initialize_database():
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS currencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            value REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (username) VALUES (?)', (username,))
    conn.commit()
    conn.close()

def add_expense(user_id, category, amount):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO expenses (user_id, category, amount) VALUES (?, ?, ?)', (user_id, category, amount))
    conn.commit()
    conn.close()

def get_user_id(username):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username=?', (username,))
    user_id = cursor.fetchone()
    conn.close()
    return user_id[0] if user_id else None

def get_expenses(user_id):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category', (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def add_category(user_id, category):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO categories (user_id, category) VALUES (?, ?)', (user_id, category))
    conn.commit()
    conn.close()

def get_categories(user_id):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category FROM categories WHERE user_id=?', (user_id,))
    categories = cursor.fetchall()
    conn.close()
    return [category[0] for category in categories]

def set_fixed_currency_values():
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO currencies (name, value, date) VALUES (?, ?, ?)', ("Доллар США", 90.9, "фиксированная дата"))
    cursor.execute('INSERT OR REPLACE INTO currencies (name, value, date) VALUES (?, ?, ?)', ("Евро", 98.7, "фиксированная дата"))
    conn.commit()
    conn.close()

def get_currency(name):
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value, date FROM currencies WHERE name=?', (name,))
    currency = cursor.fetchone()
    conn.close()
