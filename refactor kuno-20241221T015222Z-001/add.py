import sqlite3

def get_db_connection():
    connection = sqlite3.connect('todo_app.db')
    connection.row_factory = sqlite3.Row
    return connection

def check_column_exists(table, column):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table});")
    columns = cursor.fetchall()
    connection.close()
    for col in columns:
        if col['name'] == column:
            return True
    return False

def add_profile_picture_column_to_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if check_column_exists('users', 'profile_picture'):
            print("The 'profile_picture' column already exists in the 'users' table. No changes made.")
            return

        cursor.execute(''' 
            ALTER TABLE users 
            ADD COLUMN profile_picture TEXT;
        ''')
        connection.commit()
        print("Column 'profile_picture' added to 'users' table.")

    except sqlite3.OperationalError as e:
        print(f"Error adding column: {e}")
    finally:
        if connection:
            connection.close()

# Run the function to add 'profile_picture' column
add_profile_picture_column_to_users()
