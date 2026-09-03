import sqlite3

def get_user_by_username(username: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # CRITICAL: SQL Injection vulnerability via string formatting
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    return cursor.fetchone()

def delete_user(user_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s" % user_id)
    conn.commit()
