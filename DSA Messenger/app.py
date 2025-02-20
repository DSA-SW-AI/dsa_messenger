from flask import Flask, render_template, redirect, jsonify, request, session, url_for
from flask_socketio import SocketIO, send, emit, join_room
import sqlite3
from datetime import datetime
from flask_cors import CORS
import pytz







app = Flask(__name__)
app.secret_key = 'thiskeyissupposedtobeprivateandonlyknowbytheadmin'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, supports_credentials=True)
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
        conn = get_db_connection()
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


# ---------------------------------------------------------------------------
# ✅ Function to get group by ID
def get_group_by_id(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()  # Returns (id, name) or None
    conn.close()
    return group

# ---------------------------------------------------------------------------
# ✅ Function to get messages for a group
def get_messages_for_group(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT messages.id, messages.user_id, users.firstname, users.lastname, messages.message AS content, messages.timestamp
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.group_id = ?
        ORDER BY messages.timestamp ASC
    """, (group_id,))

    g_messages = cursor.fetchall()

    # ✅ Convert Row objects to dictionaries
    messages = [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "sender_name": f"{row['firstname']} {row['lastname']}",  # Combine first and last names
            "message": row["content"] if row["content"] else "No message content",
            "timestamp": row["timestamp"]
        }
        for row in g_messages
    ]

    # Debug: Check if sender_name is being correctly added
    # print("Messages being returned:", messages)

    conn.close()
    return messages  # ✅ JSON serializable




# ---------------------------------------------------------------------------


# Assuming you know the user's timezone or have a way to determine it (e.g., stored in the session)
user_timezone = pytz.timezone('Africa/Lagos')  # Replace with the user's local timezone

# get user chats(user_id)
def get_user_chats(user_id):
    """Retrieve all user chats (groups and private)."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Ensure rows are accessible as dictionaries
    cursor = conn.cursor()

    # Fetch user's group chats with message snippet
    cursor.execute("""
        SELECT groups.id, groups.name, 'group' AS type,
            (SELECT SUBSTR(message, 1, 20) FROM messages WHERE group_id = groups.id ORDER BY timestamp DESC LIMIT 1) AS last_message,
            (SELECT timestamp FROM messages WHERE group_id = groups.id ORDER BY timestamp DESC LIMIT 1) AS timestamp
        FROM groups
        JOIN user_groups ON groups.id = user_groups.group_id
        WHERE user_groups.user_id = ?
    """, (user_id,))
    group_chats = cursor.fetchall()

    # Fetch user's private chats with message snippet
    cursor.execute("""
        SELECT private_chats.id, users.firstname || ' ' || users.lastname AS name, 'private' AS type,
            (SELECT SUBSTR(message, 1, 20) FROM messages WHERE private_chat_id = private_chats.id ORDER BY timestamp DESC LIMIT 1) AS last_message,
            (SELECT timestamp FROM messages WHERE private_chat_id = private_chats.id ORDER BY timestamp DESC LIMIT 1) AS timestamp
        FROM private_chats
        JOIN users ON (users.id = private_chats.user1_id OR users.id = private_chats.user2_id)
        WHERE (private_chats.user1_id = ? OR private_chats.user2_id = ?) AND users.id != ?
    """, (user_id, user_id, user_id))
    private_chats = cursor.fetchall()

    # Merge both chats
    all_chats = group_chats + private_chats

    # Convert results into dictionaries and format the timestamp
    formatted_chats = []
    for chat in all_chats:
        chat_dict = dict(chat)  # Convert sqlite3.Row object into a dictionary
        if chat_dict["timestamp"]:
            # Convert the timestamp to a datetime object
            utc_time = datetime.strptime(chat_dict["timestamp"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            
            # Convert UTC to user's local time
            local_time = utc_time.astimezone(user_timezone)
            
            # Format the local time
            chat_dict["timestamp"] = local_time.strftime('%H:%M')

        formatted_chats.append(chat_dict)

    # Sort by timestamp in descending order (most recent first)
    formatted_chats.sort(key=lambda x: x["timestamp"] or '', reverse=True)

    return formatted_chats


# ---------------------------------------------------------------------------
# ✅ Function to get messages for a private chat
def get_messages_for_private_chat(private_chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT messages.id, messages.user_id, users.firstname || ' ' || users.lastname AS sender_name, 
               messages.message AS content, messages.timestamp
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.private_chat_id = ?
        ORDER BY messages.timestamp ASC
    """, (private_chat_id,))

    p_chat = cursor.fetchall()  # Fetch all messages

    # Check if content is empty and add a default message
    messages = [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "sender_name": row["sender_name"],
            "message": row["content"] if row["content"] else "No message content",  # Default message
            "timestamp": row["timestamp"]
        }
        for row in p_chat
    ]

    conn.close()
    return messages

# ---------------------------------------------------------------------------
# Get Private Chat by Chat ID
def get_private_chat_by_id(chat_id):
    """Fetch details of a private chat given the chat_id"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user1_id, user2_id FROM private_chats WHERE id = ?
    """, (chat_id,))
    
    private_chat = cursor.fetchone()
    conn.close()
    return private_chat  # Returns (id, user1_id, user2_id) or None

# ---------------------------------------------------------------------------
# ✅ Function to get a private chat between two users
def get_private_chat_by_details(user1_id, user2_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM private_chats
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    """, (user1_id, user2_id, user2_id, user1_id))

    private_chat = cursor.fetchone()  # Returns (id,) or None
    conn.close()
    return private_chat[0] if private_chat else None



# ----------------------------------------------------------------------------
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

    session['group_id'] = group['group_id'] if group else None  # ✅ Store group_id safely

    # Store user details in session
    session['user_id'] = user['id']
    session['staffid'] = user['staffid']
    session['firstname'] = user['firstname']
    session['lastname'] = user['lastname']

    # print("Session Data:", dict(session))  # ✅ Debugging: Check if session is set properly

    conn.close()

    return jsonify({
        'success': True,
        'redirect': url_for('chats'),
        'firstname': user['firstname'],
        'staffid': user['staffid'],
        'group_id': session['group_id']
    })


# ---------------------------------------------------------------------------

@app.route("/chat")
def chats():
    if "user_id" not in session:
        return redirect(url_for("login"))  

    user_id = session["user_id"]
    all_chats = get_user_chats(user_id)
    
    formatted_chats = [
        {
            "id": chat["id"],
            "name": chat["name"],
            "type": chat["type"],
            "last_message": chat["last_message"] or "No messages yet",
            "timestamp": chat["timestamp"] if chat["timestamp"] else ""
        } for chat in all_chats
    ]

    return render_template("chat.html", chats=formatted_chats, firstname=session.get("firstname"), staffid=session.get("staffid"))


# ---------------------------------------------------------------------------

@app.route('/chat/<chat_type>/<int:chat_id>')
def open_chat(chat_type, chat_id):
    """Render the chat page with messages and chat details."""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))  # Ensure user is logged in

    group = None
    private_chat = None
    messages = []

    if chat_type == "group":
        group = get_group_by_id(chat_id)
        if not group:
            return "Group not found", 404
        messages = get_messages_for_group(chat_id)
    elif chat_type == "private":
        private_chat = get_private_chat_by_id(chat_id)  # ✅ Correct function
        if not private_chat:
            return "Private chat not found", 404
        messages = get_messages_for_private_chat(chat_id)
    else:
        return "Invalid chat type", 400

    return render_template(
        "chat.html",
        user_id=user_id,
        group=group,
        private_chat=private_chat,
        messages=messages,
        group_id=chat_id if chat_type == "group" else None,
        private_chat_id=chat_id if chat_type == "private" else None
    )

# ---------------------------------------------------------------------------

    
@app.route('/get_messages/<chat_type>/<int:chat_id>')
def get_chat_messages(chat_type, chat_id):
    """Fetch messages for a group or private chat (AJAX request)."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # print(f"Received request: chat_type={chat_type}, chat_id={chat_id}")  # ✅ Debugging

    try:
        if chat_type == "group":
            messages = get_messages_for_group(chat_id)
        elif chat_type == "private":
            messages = get_messages_for_private_chat(chat_id)
        else:
            return jsonify({"error": "Invalid chat type"}), 400

        return jsonify({"messages": messages})

    except Exception as e:
        # print("Error:", str(e))  # Log error
        return jsonify({"error": "Something went wrong"}), 500


# ---------------------------------------------------------------------------


@app.route("/get_messages")
def get_messages():
    chat_id = request.args.get("chat_id", type=int)
    chat_type = request.args.get("chat_type")

    if not chat_id or chat_type not in ["group", "private"]:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if chat_type == "group":
        cursor.execute("""
            SELECT m.id, m.user_id, u.firstname || ' ' || u.lastname AS sender, 
                   m.message, m.timestamp  -- ✅ Use m.message instead of m.content
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.group_id = ?
            ORDER BY m.timestamp;
        """, (chat_id,))
    else:
        cursor.execute("""
            SELECT m.id, m.user_id, u.firstname || ' ' || u.lastname AS sender, 
                   m.message, m.timestamp  -- ✅ Use m.message instead of m.content
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.private_chat_id = ?
            ORDER BY m.timestamp;
        """, (chat_id,))

    messages = [
        {
            "id": row[0],
            "user_id": row[1],
            "sender": row[2] if row[2] else "Unknown Sender",
            "message": row[3] if row[3] and row[3].strip() else "(No content)",  
            "timestamp": row[4] if row[4] else "Unknown time"
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return jsonify({"messages": messages})



# ---------------------------------------------------------------------------

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    chat_id = data.get("chat_id")
    chat_type = data.get("chat_type")
    message_text = data.get("message")

    if not chat_id or not message_text or chat_type not in ["group", "private"]:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    user_id = session["user_id"]
    timestamp = datetime.now().strftime("%H:%M")

    conn = get_db_connection()
    cursor = conn.cursor()

    if chat_type == "group":
        cursor.execute("INSERT INTO messages (group_id, user_id, message, timestamp) VALUES (?, ?, ?, ?)",
                       (chat_id, user_id, message_text, timestamp))
    else:
        cursor.execute("INSERT INTO messages (private_chat_id, user_id, message, timestamp) VALUES (?, ?, ?, ?)",
                       (chat_id, user_id, message_text, timestamp))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Message sent successfully', 'timestamp': timestamp})




@socketio.on("send_group_message")
def handle_group_message(data):
    try:
        print(f"📥 Received group message data: {data}")  # Log when the function is triggered

        chat_id = data.get("chat_id")
        message = data.get("message")
        user_id = session.get("user_id")

        if not user_id:
            print("❌ ERROR: No user ID found in session")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages (user_id, group_id, message) VALUES (?, ?, ?)
        """, (user_id, chat_id, message))
        conn.commit()

        cursor.execute("SELECT firstname, lastname FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown"

        conn.close()

        print(f"✅ Message stored in database: {message} from {sender_name}")  # Log when message is stored

        # Now, try to emit the message
        print(f"🚀 Attempting to emit message to group {chat_id}")

        emit("receive_message", {
            "chat_id": chat_id,
            "chat_type": "group",
            "user_id": user_id,
            "sender_name": sender_name,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, room=str(chat_id))

        print(f"✅ Message emitted successfully!")

    except Exception as e:
        print(f"❌ ERROR: Failed to handle group message - {str(e)}")





@socketio.on("send_private_message")
def handle_private_message(data):
    try:
        chat_id = data.get("chat_id")
        message = data.get("message")
        user_id = session.get("user_id")  # Fetch user_id from session

        if not chat_id or not message or not user_id:
            print(f"ERROR: Invalid data received - {data}")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert message into the database
        cursor.execute("""
            INSERT INTO messages (user_id, private_chat_id, message) VALUES (?, ?, ?)
        """, (user_id, chat_id, message))
        conn.commit()

        # Fetch sender's name
        cursor.execute("SELECT firstname, lastname FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown User"

        conn.close()

        print(f"✅ EMITTING MESSAGE: {message} from {sender_name} to group {chat_id}")  # Debugging line


        # Emit message to the chat room
        emit("receive_message", {
            "chat_id": chat_id,
            "chat_type": "private",
            "user_id": user_id,
            "sender_name": sender_name,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Use a standard timestamp format
        }, room=str(chat_id))

    except Exception as e:
        print(f"ERROR: Failed to handle private message - {str(e)}")


@socketio.on("join_group")
def handle_join_group(data):
    group_id = data.get("group_id")
    join_room(str(group_id))
    print(f"User joined group: {group_id}")

@socketio.on("join_private_chat")
def handle_join_private_chat(data):
    chat_id = data.get("chat_id")
    join_room(str(chat_id))
    print(f"User joined private chat: {chat_id}")


# ---------------------------------------------------------------------------
# search bar
@app.route("/search_users")
def search_users():
    query = request.args.get("query", "").strip()
    user_id = session.get("user_id")  # Get logged-in user ID

    if len(query) < 2:
        return jsonify([])  # Return empty list if query is too short

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, firstname, lastname, staffid FROM users "
        "WHERE (firstname LIKE ? OR lastname LIKE ? OR staffid LIKE ?) AND id != ?",
        (f"%{query}%", f"%{query}%", f"%{query}%", user_id)
    )

    users = cursor.fetchall()
    conn.close()

    # Convert results to a list of dictionaries
    user_list = [
        {
            "id": user["id"],
            "firstname": user["firstname"],
            "lastname": user["lastname"],
            "staffid": user["staffid"],
        }
        for user in users
    ]

    return jsonify(user_list)





@app.route('/start_private_chat', methods=['POST'])
def start_private_chat():
    user1_id = session.get("user_id")  # Logged-in user
    user2_id = request.json.get("user_id")  # Selected user

    if not user1_id or not user2_id:
        return jsonify({"error": "Invalid users"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if chat already exists
    cursor.execute(
        "SELECT id FROM private_chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
        (user1_id, user2_id, user2_id, user1_id),
    )
    chat = cursor.fetchone()

    if chat:
        chat_id = chat["id"]
    else:
        # Create new private chat
        cursor.execute(
            "INSERT INTO private_chats (user1_id, user2_id) VALUES (?, ?)",
            (user1_id, user2_id),
        )
        conn.commit()
        chat_id = cursor.lastrowid

    conn.close()

    return jsonify({"chat_id": chat_id, "user_id": user2_id})


# ------------------------------

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    """Returns the logged-in user's session data to the frontend."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403

    return jsonify({
        'success': True,
        'user_id': session.get('user_id'),
        'firstname': session.get('firstname'),
        'lastname': session.get('lastname'),
        'staffid': session.get('staffid'),
        'group_id': session.get('group_id')
    })






















# Start Application
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)