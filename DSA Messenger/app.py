from flask import Flask, render_template, redirect, jsonify, request, session, url_for
from flask_socketio import SocketIO, send, emit, join_room
import sqlite3
from datetime import datetime
from flask_cors import CORS








app = Flask(__name__)
app.secret_key = 'thiskeyissupposedtobeprivateandonlyknowbytheadmin'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
# ---------------------------------------------------------------------------

# All Defined Functions

# Timestamp
def format_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')

# ---------------------------------------------------------------------------

# Initiate Database Connections
def get_db_connection():
    conn = sqlite3.connect('chatdatabase.db', check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------------------------

# link user to respective group
def link_user_to_group(user_id, directorate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find the group ID for the directorate
    cursor.execute("SELECT id FROM groups WHERE name = ?", (directorate,))
    group = cursor.fetchone()
    
    if group:
        group_id = group[0]
        cursor.execute("INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)", (user_id, group_id))
        print(f"User {user_id} linked to {directorate} group (ID: {group_id})")

    # Ensure the user is also added to "CIVILIAN STAFF"
    cursor.execute("SELECT id FROM groups WHERE name = 'CIVILLIAN STAFF'")
    civilian_group = cursor.fetchone()

    if civilian_group:
        civilian_group_id = civilian_group[0]
        cursor.execute("INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)", (user_id, civilian_group_id))
        print(f"User {user_id} also linked to CIVILLIAN STAFF group (ID: {civilian_group_id})")
    else:
        print("CIVILLIAN STAFF group not found!")

    conn.commit()
    conn.close()

# Get User function from session
def getUsers():
    try:
        conn = sqlite3.connect('chatdatabase.db')
        cursor = conn.cursor()

        # Get current user's first and last name from session
        logged_in_firstname = session.get('firstname')
        logged_in_lastname = session.get('lastname')

        # Print session values to check if they're correct
        print(f"Logged-in user: {logged_in_firstname} {logged_in_lastname}")

        # Fetch all users except the logged-in user
        cursor.execute("""
            SELECT firstname, lastname FROM users 
            WHERE NOT (firstname = ? AND lastname = ?)
        """, (logged_in_firstname, logged_in_lastname))

        users = cursor.fetchall()

        # ✅ Print raw user data from DB
        print("Raw users from DB:", users)

        conn.close()
        return users  # List of users excluding the logged-in user
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

# ---------------------------------------------------------------------------

# Insert user into Directorate
def insert():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups")
    print("Groups in database:", cursor.fetchall())

    # List of directorates
    directorates = ["DEO", "DCS", "DNPT", "DLSO", "DCYBER", "DFA", "DLOG", "DPPR", "CDSA", "CIVILLIAN STAFF"]

    for directorate in directorates:
        cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (directorate,))

    conn.commit()
    conn.close()

# insert()
# ---------------------------------------------------------------------------

# Function to get group by ID from SQLite
def get_group_by_id(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()  # Returns a tuple (id, name)
    conn.close()
    return group

# ---------------------------------------------------------------------------

# Function to get messages for the group
def get_messages_for_group(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.user_id, m.message, m.timestamp
        FROM messages m
        WHERE m.group_id = ?
        ORDER BY m.timestamp ASC
    """, (group_id,))
    messages = cursor.fetchall()  # Fetch all messages
    conn.close()
    return messages

# ---------------------------------------------------------------------------

# function to get users in a group
def get_users_in_group(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.firstname, u.lastname, u.directorate
        FROM users u
        JOIN user_groups ug ON u.id = ug.user_id
        WHERE ug.group_id = ?
    """, (group_id,))
    users_in_group = cursor.fetchall()  # Fetch all users in the group
    conn.close()
    return users_in_group

# ALL Defined Function End
# ---------------------------------------------------------------------------

# App HomePage Route
@app.route('/')
def index():
    return render_template("home.html")

# ---------------------------------------------------------------------------

# App Register Page Route
@app.route('/register')
def register():
    directorates = ["DEO", "DCS", "DNPT", "DLSO", "DCYBER", "DFA", "DLOG", "DPPR", "CDSA"]  # Load from database if needed
    return render_template("register.html", directorates=directorates)

# ---------------------------------------------------------------------------

# Registration Form Route
@app.route('/submit_register', methods=['POST'])
def submit():
    data = request.get_json()

    staffid = data.get('staffid')
    firstname = data.get('fname')
    lastname = data.get('lname')
    directorate = data.get('directorate')
    password = data.get('password')
    con_password = data.get('con_password')

    if not all([staffid, firstname, lastname, directorate, password, con_password]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    if password != con_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if staff ID already exists
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE staffid = ?', (staffid,))
    result = cursor.fetchone()
    if result['count'] > 0:
        conn.close()
        return jsonify({'success': False, 'error': 'Staff ID already exists'}), 400

    # Insert the user into the database
    cursor.execute(
        'INSERT INTO users (staffid, firstname, lastname, directorate, password) VALUES (?, ?, ?, ?, ?)',
        (staffid, firstname, lastname, directorate, password)
    )
    conn.commit()

    # Get the user_id of the last inserted user
    user_id = cursor.lastrowid

    # Link the user to the group based on directorate
    link_user_to_group(user_id, directorate)
    conn.close()

    return jsonify({'success': True})

# ---------------------------------------------------------------------------

# App Login Page Route 
@app.route('/login')
def login_success():
    return render_template('login.html')

# ---------------------------------------------------------------------------

# App login Verifcation Route

@app.route('/submit_login', methods=['POST'])
def login():
    # Get JSON data from the request
    data = request.get_json()

    staffid = data.get('staffid')
    password = data.get('password')

    # Validate inputs
    if not staffid or not password:
        return jsonify({'success': False, 'error': 'Staff ID and Password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE staffid = ?', (staffid,))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid Staff ID'}), 400

    if user['password'] != password:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid Password'}), 400

    # Fetch the user's group
    cursor.execute("SELECT group_id FROM user_groups WHERE user_id = ?", (user['id'],))
    group = cursor.fetchone()

    if group:
        session['group_id'] = group['group_id']  # ✅ Store group_id in session
    else:
        session['group_id'] = None  # Handle case where user has no group

    # Login successful
    session['user_id'] = user['id']
    session['staffid'] = user['staffid']
    session['firstname'] = user['firstname']
    session['lastname'] = user['lastname']

    conn.close()

    return jsonify({
        'success': True,
        'redirect': url_for('chat'),
        'firstname': user['firstname'],
        'staffid': user['staffid'],
        'group_id': session['group_id']  # ✅ Return group_id to frontend
    })


# ---------------------------------------------------------------------------

# Chat Page Route
@app.route('/chat')
def chat():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    # Retrieve user details from the session
    user_id = session.get('user_id')
    staffid = session.get('staffid')
    firstname = session.get('firstname')
    lastname = session.get('lastname')

    # ✅ Fetch only groups where the user is a member
    conn = sqlite3.connect('chatdatabase.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.id, g.name 
        FROM groups g
        JOIN user_groups ug ON g.id = ug.group_id
        WHERE ug.user_id = ?
    """, (user_id,))

    groups = cursor.fetchall()

    print("User's groups:", groups)  # Debugging output

    conn.close()

    return render_template(
        'chat.html',
        user_id=user_id,
        staffid=staffid,
        firstname=firstname,
        lastname=lastname,
        groups=groups,  # Send only relevant groups to frontend
        group_id=session.get('group_id')
    )

# ---------------------------------------------------------------------------

# Route for Chat Directorate/Groups

@app.route('/chat/<int:group_id>')
def chat_page(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    user_id = session['user_id']
    staffid = session.get('staffid')
    firstname = session.get('firstname')

    # Fetch the group by its ID
    group = get_group_by_id(group_id)
    if not group:
        return "Group not found", 404

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch users in the group
    cursor.execute("""
        SELECT u.firstname, u.lastname, u.directorate
        FROM users u
        JOIN user_groups ug ON u.id = ug.user_id
        WHERE ug.group_id = ?
    """, (group_id,))
    users = cursor.fetchall()

    # Fetch messages properly
    cursor.execute("""
        SELECT messages.id, messages.user_id, users.firstname, users.lastname, 
               messages.message, messages.timestamp
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.group_id = ?
        ORDER BY messages.timestamp ASC
    """, (group_id,))
    messages = cursor.fetchall()  # ✅ This is now correct

    conn.close()

    return render_template('chat.html', group=group, messages=messages, users=users, 
                           user_id=user_id, firstname=firstname, staffid=staffid, 
                           format_timestamp=format_timestamp, group_id=group_id)


# ---------------------------------------------------------------------------

# Directorate Group Chats/
@app.route('/group_chat/<group_name>')
def group_chat(group_name):

    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id'] 
    # user_id = session.get('user_id')
    staffid = session.get('staffid')
    firstname = session.get('firstname') # Get user_id from session

    conn = get_db_connection()
    
    # Fetch the group details
    group = conn.execute("SELECT * FROM groups WHERE name = ?", (group_name,)).fetchone()

    if not group:
        conn.close()
        return "Group not found", 404  # Prevents 'group' being undefined
    
    group_id = group["id"]

    # Fetch messages for this group
    messages = conn.execute(
        """SELECT messages.message, users.firstname, users.lastname 
           FROM messages 
           JOIN users ON messages.user_id = users.id 
           WHERE messages.group_id = ? 
           ORDER BY messages.id ASC""",
        (group_id,)
    ).fetchall()
    
    # Fetch users in this group
    users_in_group = conn.execute(
        """SELECT users.id, users.firstname, users.lastname 
           FROM users 
           JOIN user_groups ON users.id = user_groups.user_id 
           WHERE user_groups.group_id = ?""",
        (group_id,)
    ).fetchall()
    
    conn.close()

    return render_template('chat.html', group=dict(group), messages=messages, users=users_in_group, user_id=user_id, firstname=firstname, staffid=staffid)

# ---------------------------------------------------------------------------



@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    
    print("Received data:", data)  # Debugging

    # Ensure the request payload is valid JSON
    if not isinstance(data, dict):
        print("⚠️ Error: Request data is not JSON")
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400

    message = data.get('message')
    group_id = data.get('group_id')
    user_id = session.get('user_id')  # Get logged-in user from session

    print(f"Session User ID: {user_id}, Group ID: {group_id}, Message: {message}")  # Debugging

    # Check if user is logged in
    if not user_id:
        print("⚠️ Error: User not logged in")
        return jsonify({'success': False, 'error': 'User not logged in'}), 403  # Unauthorized

    # Ensure message and group_id are present
    if message is None or group_id is None:
        print("⚠️ Error: Missing message or group_id")
        return jsonify({'success': False, 'error': 'Missing message or group_id'}), 400

    # Ensure group_id is an integer
    try:
        group_id = int(group_id)
    except (TypeError, ValueError):
        print("⚠️ Error: Invalid group_id format")
        return jsonify({'success': False, 'error': 'Invalid group_id format'}), 400

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Store message in the database
        cursor.execute('''
            INSERT INTO messages (user_id, group_id, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, group_id, message, timestamp))
        conn.commit()
        print("✅ Message successfully saved to database!")  # Debugging

        # Fetch sender details
        cursor.execute('SELECT firstname, lastname FROM users WHERE id = ?', (user_id,))
        sender = cursor.fetchone()
        sender_name = f"{sender[0]} {sender[1]}" if sender else "Unknown"

        # Emit message via WebSocket
        socketio.emit('receive_message', {
            'message': message,
            'group_id': group_id,
            'user_id': user_id,
            'sender_name': sender_name,
            'timestamp': timestamp
        }, room=group_id)

        return jsonify({'success': True, 'message': message, 'timestamp': timestamp})

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500  # Internal Server Error

    finally:
        conn.close()  # Ensure DB connection is closed



@socketio.on('send_message')
def handle_send_message(data):
    """Handle real-time messages via WebSocket."""
    print(f"DEBUG: Received send_message event with data: {data}")  

    message = data.get('message', '').strip()  # Ensure message is not empty
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not message or not group_id or not user_id:
        print("ERROR: Invalid message data received, ignoring event.")
        return

    conn = None
    try:
        # Save message in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, group_id, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, group_id, message, timestamp))
        conn.commit()
        print("DEBUG: Message stored successfully.")

        # Fetch sender details
        cursor.execute('SELECT firstname, lastname FROM users WHERE id = ?', (user_id,))
        sender = cursor.fetchone()
        sender_name = f"{sender[0]} {sender[1]}" if sender else "Unknown"

        # Broadcast message to group
        emit('receive_message', {
            'message': message,
            'group_id': group_id,
            'user_id': user_id,
            'sender_name': sender_name,
            'timestamp': timestamp
        }, room=group_id, broadcast=True)
        print("DEBUG: Message emitted successfully.")

    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        emit('error', {'error': str(e)})  # Notify client about the error

    finally:
        if conn:
            conn.close()  # Ensure DB connection is closed


@socketio.on('join_group')
def handle_join_group(data):
    """Handle user joining a group."""
    print(f"DEBUG: Received join_group event with data: {data}")  
    group_id = data.get('group_id')

    if not group_id:
        print("ERROR: Invalid group_id received, ignoring event.")
        return

    join_room(group_id)
    print(f"DEBUG: User joined group {group_id}")

    emit('user_joined', {'group_id': group_id}, room=group_id)
    print(f"DEBUG: Emitted user_joined event to group {group_id}.")



# ---------------------------------------------------------------------------




# Start Application
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005)