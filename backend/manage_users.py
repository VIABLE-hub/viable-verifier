
import sqlite3
from werkzeug.security import generate_password_hash
import sys
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'studentvc.sqlite')

def list_users():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM user")
        users = cursor.fetchall()
        print("\nExisting Users:")
        print("-" * 30)
        for user in users:
            print(f"ID: {user[0]}, Email: {user[1]}")
        print("-" * 30)
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

def reset_password(email, new_password):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM user WHERE name = ?", (email,))
        user_row = cursor.fetchone()
        
        if not user_row:
            print(f"User '{email}' not found.")
            return

        # Generate hash
        pwhash = generate_password_hash(new_password)
        
        # Update
        cursor.execute("UPDATE user SET password_hash = ? WHERE name = ?", (pwhash, email))
        conn.commit()
        print(f"✅ Password for '{email}' successfully updated.")
        
    except Exception as e:
        print(f"Error updating password: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_users.py list")
        print("  python manage_users.py reset <email> <new_password>")
        sys.exit(1)

    action = sys.argv[1]
    
    if action == "list":
        list_users()
    elif action == "reset":
        if len(sys.argv) != 4:
            print("Usage: python manage_users.py reset <email> <new_password>")
        else:
            reset_password(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {action}")
