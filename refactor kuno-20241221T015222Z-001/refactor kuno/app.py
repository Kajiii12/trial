import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    connection = sqlite3.connect('todo_app.db')
    connection.row_factory = sqlite3.Row
    return connection

# Initialize SQLite database and create the users and tasks table if they don't exist
def initialize_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create the tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    connection.commit()
    connection.close()

initialize_db()

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))  # Redirect logged-in users to the dashboard
    return render_template("login.html")  # Landing page

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Handle registration logic
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        # Insert user data into the database
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (first_name, last_name, email, password_hash))
            connection.commit()
            connection.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Error: Email already exists.', 'danger')
        except Exception as e:
            flash(f'Error: Unable to register. {str(e)}', 'danger')

    return render_template('registration.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            connection.close()

            if user:
                if check_password_hash(user[4], password):
                    session['user_id'] = user[0]
                    session['user_name'] = f"{user[1]} {user[2]}"
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)  # Clear session cookie
    flash('You have been logged out.', 'info')
    return response

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    user_first_name = session.get('user_name', 'User').split()[0]
    
    # Fetch tasks for the logged-in user
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM tasks WHERE user_id = ?
    ''', (session['user_id'],))
    tasks = cursor.fetchall()
    connection.close()

    return render_template("dashboard.html", user_first_name=user_first_name, tasks=tasks)

# @app.route("/add_task", methods=["GET", "POST"])
# def add_task():
#     if 'user_id' not in session:
#         flash('Please log in to add tasks.', 'warning')
#         return redirect(url_for('login'))

#     if request.method == "POST":
#         title = request.form["title"]
#         description = request.form["description"]
#         due_date = request.form["due_date"]

#         # Insert the new task into the database
#         connection = get_db_connection()
#         cursor = connection.cursor()
#         cursor.execute('''
#             INSERT INTO tasks (user_id, title, description, due_date)
#             VALUES (?, ?, ?, ?)
#         ''', (session['user_id'], title, description, due_date))
#         connection.commit()
#         connection.close()

#         flash('Task added successfully!', 'success')
#         return redirect(url_for('dashboard'))

#     return render_template('add_task.html')

@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if 'user_id' not in session:
        flash('Please log in to add tasks.', 'warning')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not title or not description or not due_date:
            flash("All fields are required to add a task.", "danger")
            return redirect(url_for('add_task'))

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, due_date)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], title, description, due_date))
        connection.commit()
        connection.close()

        flash('Task added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html')


@app.route("/update_task/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    if 'user_id' not in session:
        flash('Please log in to update tasks.', 'warning')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    task = cursor.fetchone()

    if not task:
        connection.close()
        flash("Task not found or you don't have permission to edit it.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not title or not description or not due_date:
            flash("All fields are required to update the task.", "danger")
            return redirect(url_for('update_task', task_id=task_id))

        cursor.execute('''
            UPDATE tasks
            SET title = ?, description = ?, due_date = ?
            WHERE id = ? AND user_id = ?
        ''', (title, description, due_date, task_id, session['user_id']))
        connection.commit()
        connection.close()

        flash('Task updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    connection.close()
    return render_template('update_task.html', task=task)


@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if 'user_id' not in session:
        flash('Please log in to delete tasks.', 'warning')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    connection.commit()
    connection.close()

    flash('Task deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route("/main_dashboard")
def main_dashboard():
    return render_template('main_dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)
