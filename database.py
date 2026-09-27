import sqlite3

DB_NAME = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_warns (
            chat_id INTEGER,
            user_id INTEGER,
            warn_count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            is_premium INTEGER DEFAULT 0,
            custom_bad_words TEXT DEFAULT ''
        )
    ''')

    conn.commit()
    conn.close()

def get_warn_count(chat_id: int, user_id: int) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT warn_count FROM user_warns WHERE chat_id = ? AND user_id = ?", 
        (chat_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def add_warn(chat_id: int, user_id: int) -> int:
    current_warns = get_warn_count(chat_id, user_id) + 1
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_warns (chat_id, user_id, warn_count)
        VALUES (?, ?, ?)
        ON CONFLICT(chat_id, user_id) DO UPDATE SET warn_count = ?
    ''', (chat_id, user_id, current_warns, current_warns))
    conn.commit()
    conn.close()
    return current_warns

def reset_warns(chat_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_warns WHERE chat_id = ? AND user_id = ?", 
        (chat_id, user_id)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database Initialization Success")