import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = r'C:\Users\Joshua Ean\Desktop\refactor kuno-20241221T015222Z-001\refactor kuno\static\avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mail = Mail(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper function for database connection
def get_db_connection():
    connection = sqlite3.connect('todo_app.db')
    connection.row_factory = sqlite3.Row
    return connection

# Initialize SQLite database and create tables
def initialize_db():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Create the users table with an 'is_blocked' field to track blocked status
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user', -- Added role field with default 'user'
                is_blocked BOOLEAN DEFAULT 0 -- Add is_blocked field (0 = not blocked, 1 = blocked)
            )
        ''')

        # Create the tasks table (unchanged)
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date DATE NOT NULL,
                priority TEXT DEFAULT 'LOW',
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        connection.commit()
        connection.close()
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")


initialize_db()

# Home route
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        role = request.form.get("role", "user")  # Default role is 'user'
        profile_picture = request.form.get("profile_picture")  # Capture the Base64 image data

        if not first_name or not last_name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        # Password hashing
        password_hash = generate_password_hash(password)

        try:
            # Save the profile picture if available
            if profile_picture:
                # Remove the data URL prefix (data:image/jpeg;base64,)
                img_data = profile_picture.split(",")[1]
                img_data = base64.b64decode(img_data)
                
                # Convert binary data to image using PIL
                image = Image.open(BytesIO(img_data))
                
                # Save the image with the first name as the filename
                avatar_filename = f"{first_name.lower()}.jpg"
                avatar_path = os.path.join(UPLOAD_FOLDER, avatar_filename)
                image.save(avatar_path)

            # Insert the user into the database
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(''' 
                INSERT INTO users (first_name, last_name, email, password_hash, role, profile_picture)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, password_hash, role, avatar_filename if profile_picture else None))
            connection.commit()
            connection.close()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        except sqlite3.IntegrityError:
            flash('Error: Email already exists.', 'danger')
        except Exception as e:
            flash(f'Error: Unable to register. {str(e)}', 'danger')

    return render_template('registration.html')

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        if not email or not password:
            flash("Both email and password are required.", "danger")
            return redirect(url_for('login'))

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            connection.close()

            if user:
                if user['is_blocked']:
                    flash('Your account is blocked. Please contact an admin.', 'danger')
                    return redirect(url_for('login'))

                if check_password_hash(user["password_hash"], password):
                    session['user_id'] = user["id"]
                    session['user_name'] = f"{user['first_name']} {user['last_name']}"
                    session['role'] = user['role']  # Store role in session
                    flash('Login successful!', 'success')

                    # Redirect to the appropriate dashboard based on user role
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))  # Admin dashboard
                    else:
                        return redirect(url_for('dashboard'))  # Regular user dashboard

            flash('Invalid email or password.', 'danger')
        except Exception as e:
            logging.error(f"Login failed: {e}")
            flash("Error: Unable to login. Please try again.", 'danger')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Dashboard route (User dashboard)
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    # Get user's first name
    user_first_name = session.get('user_name', 'User').split()[0]

    # Construct the avatar filename and path
    avatar_filename = f"{user_first_name.lower()}.jpg"
    avatar_path = os.path.join(
        app.static_folder, 'avatars', avatar_filename
    )

    # Check if the avatar file exists
    if not os.path.isfile(avatar_path):
        avatar_filename = "default.jpg"  # Fallback to default avatar

    # Generate the avatar URL for the template
    avatar_url = url_for('static', filename=f"avatars/{avatar_filename}")

    # Fetch tasks for the logged-in user
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM tasks WHERE user_id = ?
        ORDER BY due_date ASC, priority DESC
    ''', (session['user_id'],))
    tasks = cursor.fetchall()
    connection.close()

    return render_template(
        "dashboard.html",
        user_first_name=user_first_name,
        user_avatar_url=avatar_url,
        tasks=tasks
    )

# Admin Dashboard route
@app.route("/admin_dashboard")
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('dashboard'))

    # Fetch all users and tasks for the admin
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()

    connection.close()

    return render_template('admin_dashboard.html', users=users, tasks=tasks)

# Ensure that the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Secure the filename and save the file with user's first name
        filename = secure_filename(file.filename)
        user_first_name = session.get('user_name', 'default').split()[0].lower()
        avatar_filename = f"{user_first_name}.{filename.rsplit('.', 1)[1].lower()}"
        
        # Save the file to the avatar folder
        file.save(os.path.join(UPLOAD_FOLDER, avatar_filename))
        
        # Flash success message and redirect to dashboard
        flash('Profile picture uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('File type not allowed.', 'error')
        return redirect(request.url)

# Add task route
@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if 'user_id' not in session:
        flash('Please log in to add tasks.', 'warning')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "").strip()
        priority = request.form.get("priority", "LOW").strip()

        if not title or not description or not due_date:
            flash("All fields are required to add a task.", "danger")
            return redirect(url_for('add_task'))

        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d')  # Validate date format
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('add_task'))

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, due_date, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], title, description, due_date, priority))
        connection.commit()
        connection.close()

        flash('Task added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html')

# Update task route
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
        priority = request.form.get("priority", "LOW").strip()
        status = request.form.get("status", "Pending").strip()

        if not title or not description or not due_date:
            flash("All fields are required to update the task.", "danger")
            return redirect(url_for('update_task', task_id=task_id))

        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d')  # Validate date format
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('update_task', task_id=task_id))

        cursor.execute('''
            UPDATE tasks
            SET title = ?, description = ?, due_date = ?, priority = ?, status = ?
            WHERE id = ? AND user_id = ?
        ''', (title, description, due_date, priority, status, task_id, session['user_id']))
        connection.commit()
        connection.close()

        flash('Task updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    connection.close()
    return render_template('update_task.html', task=task)

# Delete task route
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

#################################################

# Route to fetch all users
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, first_name || " " || last_name AS username, email, role, is_blocked FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])  # Convert rows to dictionaries

# Route to block/unblock a user
@app.route('/block-user', methods=['PUT'])
def block_user():
    data = request.get_json()
    user_id = data.get('id')
    is_blocked = data.get('is_blocked')

    if user_id is None or is_blocked is None:
        return jsonify({'success': False, 'error': 'Invalid input.'}), 400

    connection = get_db_connection()
    connection.execute(
        'UPDATE users SET is_blocked = ? WHERE id = ?',
        (is_blocked, user_id)
    )
    connection.commit()
    connection.close()

    return jsonify({'success': True, 'message': f'User {user_id} has been {"blocked" if is_blocked else "unblocked"}.'})


# Route to delete a user
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = get_db_connection()
    connection.execute('DELETE FROM users WHERE id = ?', (user_id,))
    connection.commit()
    connection.close()
    return jsonify({'message': f'User {user_id} deleted.'})

################################################

@app.route('/api/tasks', methods=['GET'])
def get_user_tasks():
    connection = get_db_connection()

    # Fetch tasks with user details (excluding admins)
    query = """
        SELECT 
            tasks.id AS task_id,
            tasks.title,
            tasks.description,
            tasks.due_date,  -- Changed from 'deadline' to 'due_date'
            tasks.status,
            users.first_name,
            users.last_name,
            users.email
        FROM tasks
        INNER JOIN users ON tasks.user_id = users.id  -- Using 'user_id' instead of 'assigned_to'
        WHERE users.role != 'admin'
        ORDER BY users.first_name, users.last_name;
    """
    tasks = connection.execute(query).fetchall()
    connection.close()

    # Group tasks by concatenated first_name and last_name
    grouped_tasks = {}
    for task in tasks:
        # Concatenate first_name and last_name to create the full name (username)
        username = f"{task['first_name']} {task['last_name']}"
        
        # Group tasks by username
        if username not in grouped_tasks:
            grouped_tasks[username] = []
        
        grouped_tasks[username].append({
            'task_id': task['task_id'],
            'title': task['title'],
            'description': task['description'],
            'due_date': task['due_date'],  # Changed from 'deadline' to 'due_date'
            'status': task['status'],
            'email': task['email']
        })

    return jsonify(grouped_tasks)


@app.route('/api/notify/<int:task_id>', methods=['POST'])
def notify_user(task_id):
    connection = get_db_connection()

    # Fetch the task and associated user data
    task = connection.execute("""
        SELECT tasks.title, tasks.due_date, users.email, 
               users.first_name || ' ' || users.last_name AS username, users.id as user_id
        FROM tasks
        INNER JOIN users ON tasks.user_id = users.id
        WHERE tasks.id = ?
    """, (task_id,)).fetchone()

    if not task:
        connection.close()
        return jsonify({'success': False, 'error': 'Task not found.'}), 404

    # Create the notification message
    message = f"Task '{task['title']}' is nearing its due date: {task['due_date']}"

    # Insert the notification into the database
    connection.execute("""
        INSERT INTO notifications (user_id, task_id, message, status)
        VALUES (?, ?, ?, 'Unread')
    """, (task['user_id'], task_id, message))
    connection.commit()
    connection.close()

    return jsonify({
        'success': True,
        'message': f"Notification sent to {task['username']} ({task['email']}) about task '{task['title']}'."
    })

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id')  # Assume user ID is stored in session after login
    if not user_id:
        return jsonify({'success': False, 'error': 'User not authenticated.'}), 401

    connection = get_db_connection()
    notifications = connection.execute("""
        SELECT message, created_at, status
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    connection.close()

    return jsonify([dict(row) for row in notifications])



# Route to generate a user activity report
@app.route('/api/reports', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')

    if report_type == 'user_activity':
        # Example: Get user login activity (excluding 'admin' users)
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('''
            SELECT users.first_name, users.last_name, COUNT(tasks.id) AS task_count
            FROM users
            LEFT JOIN tasks ON tasks.user_id = users.id
            WHERE users.role != 'admin'  -- Exclude users with 'admin' role
            GROUP BY users.id
            ORDER BY task_count DESC
        ''')
        user_activity_report = cursor.fetchall()
        connection.close()

        # Return the report as a JSON response
        return jsonify([dict(report) for report in user_activity_report])

    elif report_type == 'task_completion':
        # Example: Get task completion status for each user (excluding 'admin' users)
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('''
            SELECT users.first_name, users.last_name, tasks.status, COUNT(tasks.id) AS task_count
            FROM tasks
            INNER JOIN users ON tasks.user_id = users.id
            WHERE users.role != 'admin'  -- Exclude users with 'admin' role
            GROUP BY users.id, tasks.status
            ORDER BY users.first_name, tasks.status
        ''')
        task_completion_report = cursor.fetchall()
        connection.close()

        # Return the report as a JSON response
        return jsonify([dict(report) for report in task_completion_report])

    else:
        return jsonify({'error': 'Invalid report type. Valid types are "user_activity" and "task_completion".'}), 400



if __name__ == '__main__':
    app.run(debug=True)
