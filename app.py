from flask import Flask, request, jsonify, render_template, redirect, Request, url_for, session, send_from_directory, Response
from pymongo import MongoClient
import certifi
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os
import re
import gridfs
from gridfs.errors import NoFile
from pymongo.errors import PyMongoError







app = Flask(__name__)
app.secret_key = 'thiskeyissupposedtobeprivateandonlyknowbytheadmin'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, supports_credentials=True)
app.permanent_session_lifetime = timedelta(hours=2)


# Use a single connection for both PyMongo and GridFS
MONGO_URI = "mongodb+srv://udofiaubong10:qAWzNlJT6x2vSCdb@dsamessenger.tqp9u.mongodb.net/chatDatabase"
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())  # Secure TLS connection

# Set up database and GridFS
db = mongo_client["chatDatabase"]
fs = gridfs.GridFS(db)  # GridFS instance


users = db["users"]
users_collection = db["users"]
groups_collection = db["groups"]
user_groups_collection = db["user_groups"]
private_chats_collection = db["private_chats"]
messages_collection = db["messages"]



# Optional: If you still want to use Flask-PyMongo
app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)  # Uses the same MongoDB connection


  
# ------------------------------------------------------------------------


UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mp3", "pdf", "docx"}

# ---------------------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------------------------

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------------------------------------------------------------------
# @app.route("/upload", methods=["POST"])
# def upload_file():
#     if "file" not in request.files:
#         return jsonify({"success": False, "error": "No file provided"}), 400

#     file = request.files["file"]

#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#         file.save(file_path)

#         print("✅ File uploaded successfully:", file_path)

#         return jsonify({"success": True, "file_url": f"/uploads/{filename}"})

#     return jsonify({"success": False, "error": "Invalid file type"}), 400

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join("uploads", filename)
    file.save(file_path)

    file_url = f"/uploads/{filename}"

    return jsonify({"success": True, "file_url": file_url}), 200

# ---------------------------------------------------------------------------

# All Defined Functions

# Timestamp
def format_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')

# ---------------------------------------------------------------------------
# Set up database and GridFs
def get_db_connection():
    MONGO_URI = "mongodb+srv://udofiaubong10:qAWzNlJT6x2vSCdb@dsamessenger.tqp9u.mongodb.net/chatDatabase"
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())  # Adjust connection string if needed
    
    # Set up database and GridFS
    db = mongo_client["chatDatabase"]
    return db
# ---------------------------------------------------------------------------
# ✅ Function to get a group by ID
def get_group_by_id(group_id):
    db = get_db_connection()
    group = db.groups.find_one({"_id": ObjectId(group_id)}, {"_id": 1, "name": 1})
    if group:
        group["id"] = str(group["_id"])  # Convert ObjectId to string for JSON compatibility
        del group["_id"]
    return group  # Returns a dictionary or None

# ---------------------------------------------------------------------------

def get_messages_for_group(group_id):
    db = get_db_connection()

    try:
        # Validate ObjectId
        group_id = ObjectId(group_id)

        messages_cursor = db.messages.find(
            {"group_id": group_id},
            {"_id": 1, "user_id": 1, "message": 1, "message_type": 1, "timestamp": 1}
        ).sort("timestamp", 1)

        messages = []
        for msg in messages_cursor:
            user = db.users.find_one({"_id": ObjectId(msg["user_id"])}, {"firstname": 1, "lastname": 1})
            sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown User"

            # Handle different message types
            file_path = None
            if msg.get("message_type") in ["image", "file", "video", "audio"] and msg.get("message"):
                file_path = f"/uploads/{msg['message']}" if not msg["message"].startswith("/uploads/") else msg["message"]

            messages.append({
                "id": str(msg["_id"]),
                "user_id": str(msg["user_id"]),
                "sender": sender_name,
                "message": msg["message"] if msg["message_type"] == "text" else None,
                "message_type": msg["message_type"],
                "file_path": file_path,
                "timestamp": str(msg.get("timestamp", "Unknown time"))  # Convert to string
            })

        return messages

    except (PyMongoError, Exception) as e:
        print(f"❌ Error fetching group messages: {e}")
        return []



def get_messages_for_private_chat(private_chat_id):
    db = get_db_connection()

    try:
        # Validate ObjectId
        private_chat_id = ObjectId(private_chat_id)

        messages_cursor = db.messages.find(
            {"private_chat_id": private_chat_id},
            {"_id": 1, "user_id": 1, "message": 1, "message_type": 1, "timestamp": 1}
        ).sort("timestamp", 1)

        messages = []
        for msg in messages_cursor:
            user = db.users.find_one({"_id": ObjectId(msg["user_id"])}, {"firstname": 1, "lastname": 1})
            sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown User"

            # Handle different message types
            file_path = None
            if msg.get("message_type") in ["image", "file", "video", "audio"] and msg.get("message"):
                file_path = f"/uploads/{msg['message']}" if not msg["message"].startswith("/uploads/") else msg["message"]

            messages.append({
                "id": str(msg["_id"]),
                "user_id": str(msg["user_id"]),
                "sender": sender_name,
                "message": msg["message"] if msg["message_type"] == "text" else None,
                "message_type": msg["message_type"],
                "file_path": file_path,
                "timestamp": str(msg.get("timestamp", "Unknown time"))  # Convert to string
            })

        return messages

    except (PyMongoError, Exception) as e:
        print(f"❌ Error fetching private messages: {e}")
        return []


# ---------------------------------------------------------------------------
# ✅ Function to get a private chat by ID
def get_private_chat_by_id(chat_id):
    db = get_db_connection()
    private_chat = db.private_chats.find_one({"_id": ObjectId(chat_id)}, {"_id": 1, "user1_id": 1, "user2_id": 1})
    if private_chat:
        private_chat["id"] = str(private_chat["_id"])
        private_chat["user1_id"] = str(private_chat["user1_id"])
        private_chat["user2_id"] = str(private_chat["user2_id"])
        del private_chat["_id"]
    return private_chat  # Returns a dictionary or None

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

# App HomePage Route
@app.route('/')
def index():
    return render_template("home.html")

# ---------------------------------------------------------------------------

# App Register Page Route

@app.route('/register')
def register():
    # Fetch all groups **except** the "Civillian Staff" group
    groups = list(db.groups.find({"name": {"$ne": "CIVILLIAN STAFF"}}, {"_id": 1, "name": 1}))

    return render_template("register.html", groups=groups)

# -------------------------------------------------------------------
# Registration Form Route
@app.route('/submit_register', methods=['POST'])
def submit_register():
    try:
        staffid = request.form.get('staffid')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        directorate = request.form.get('group_id')
        password = request.form.get('password')
        con_password = request.form.get('con_password')
        profile_picture = request.files.get('profile_picture')

        if not all([staffid, fname, lname, directorate, password, con_password, profile_picture]):
            return jsonify({"success": False, "error": "All fields are required"}), 400

        if password != con_password:
            return jsonify({"success": False, "error": "Passwords do not match"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Check if the user already exists
        existing_user = db.users.find_one({"staffid": staffid})
        if existing_user:
            return jsonify({"success": False, "error": "User with this Staff ID already exists"}), 400



        # Remove previous profile picture if exists
        existing_user_pic = db.users.find_one({"staffid": staffid}, {"image": 1})
        if existing_user_pic and "image" in existing_user_pic:
            fs.delete(ObjectId(existing_user_pic["image"]))

        # Store new profile picture in GridFS
        profile_picture_id = fs.put(profile_picture, filename=profile_picture.filename, content_type=profile_picture.content_type)


        # Get the selected group name
        group = db.groups.find_one({"_id": ObjectId(directorate)})
        if not group:
            return jsonify({"success": False, "error": "Invalid group selected"}), 400
        group_name = group["name"]  # Store group name in the directorate field


        # Get the Civillian Staff group _id
        civillian_group = db.groups.find_one({"name": "CIVILLIAN STAFF"}, {"_id": 1})
        if not civillian_group:
            return jsonify({"success": False, "error": "Civillian Staff group not found"}), 500


        # Insert new user into MongoDB
        user_data = {
            "staffid": staffid,
            "firstname": fname,
            "lastname": lname,
            "directorate": group_name,
            "password": hashed_password,
            "image": str(profile_picture_id),  # Store the GridFS file ID
            "groups": [ObjectId(directorate), civillian_group["_id"]]
        }
        db.users.insert_one(user_data) 

        return jsonify({"success": True}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# App login Verifcation Route
@app.route('/submit_login', methods=['POST'])
def submit_login():
    data = request.json
    staffid = data.get("staffid")
    password = data.get("password")

    user = users.find_one({"staffid": staffid})

    if user and "password" in user:
        stored_password = user["password"]

        # Use Werkzeug's check_password_hash instead of bcrypt
        if check_password_hash(stored_password, password):
            session['user_id'] = str(user["_id"])
            session['firstname'] = user['firstname']
            session['staffid'] = user['staffid']
            return jsonify({"success": True, "redirect": "/chat"})
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    else:
        return jsonify({"success": False, "error": "User not found"}), 404

# ---------------------------------------------------------------------------

@app.route('/group_image/<group_id>')
def get_group_image(group_id):
    try:
        db = get_db_connection()

        if not ObjectId.is_valid(group_id):  # Ensure valid ObjectId
            return jsonify({"success": False, "error": "Invalid group ID"}), 400

        group = db.groups.find_one({"_id": ObjectId(group_id)}, {"image": 1})
        if not group or not group.get("image"):
            return jsonify({"success": False, "error": "No image found"}), 404

        image_id = group["image"]
        if not ObjectId.is_valid(image_id):  # Ensure valid image ID
            return jsonify({"success": False, "error": "Invalid image ID"}), 400

        try:
            image_file = fs.get(ObjectId(image_id))  # Retrieve image from GridFS
        except NoFile:
            return jsonify({"success": False, "error": "Image not found in GridFS"}), 404

        return Response(image_file.read(), mimetype=image_file.content_type)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# ---------------------------
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ---------------------------------------------------------------

@app.route('/profile_picture/<user_id>')
def get_profile_picture(user_id):
    try:
        db = get_db_connection()
        print(f"Fetching profile picture for user: {user_id}")

        if not ObjectId.is_valid(user_id):  
            return jsonify({"success": False, "error": "Invalid user ID"}), 400

        user = db.users.find_one({"_id": ObjectId(user_id)}, {"image": 1})
        print(f"User data fetched: {user}")  # Debugging

        if not user or not user.get("image"):
            return jsonify({"success": False, "error": "No image found"}), 404

        image_id = user["image"]
        print(f"Image ID found: {image_id}")

        if not ObjectId.is_valid(image_id):  
            return jsonify({"success": False, "error": "Invalid image ID"}), 400

        try:
            image_file = fs.get(ObjectId(image_id))  
            print(f"Image successfully retrieved from GridFS")
        except NoFile:
            return jsonify({"success": False, "error": "Image not found in GridFS"}), 404

        return Response(image_file.read(), mimetype=image_file.content_type)

    except Exception as e:
        print(f"Error: {e}")  # Debugging
        return jsonify({"success": False, "error": str(e)}), 500


# Display in HTML
# <img src="/profile_picture/{{ user_id }}" alt="Profile Picture">
# ----------------------------------------------------------------------

# Define the user's timezone
user_timezone = pytz.timezone('Africa/Lagos')  # Update with the correct timezone

def get_user_chats(user_id):
    db = get_db_connection()

    user = db.users.find_one({"_id": ObjectId(user_id)}, {"groups": 1})
    if not user:
        return []

    # Debug: Print user data
    print("User Data:", user)

    # Get user's groups
    group_chats = list(db.groups.find(
        {"_id": {"$in": user["groups"]}},
        {"_id": 1, "name": 1, "image": 1}  # Include the group image
    ))

    # Debug: Print group chats
    print("Group Chats:", group_chats)

    # Fetch latest message for each group
    for group in group_chats:
        last_message = db.messages.find_one(
            {"group_id": group["_id"]},
            {"message": 1, "timestamp": 1},
            sort=[("timestamp", -1)]
        )
        group["type"] = "group"
        group["image"] = group.get("image", "/static/images/default-group.png")  # Use default if no image
        group["last_message"] = format_last_message(last_message["message"]) if last_message else "No messages yet"
        group["timestamp"] = format_timestamp(last_message["timestamp"]) if last_message else ""

    # Get user's private chats
    private_chats = list(db.private_chats.find(
        {"$or": [{"user1_id": ObjectId(user_id)}, {"user2_id": ObjectId(user_id)}]}
    ))

    # Debug: Print private chats
    print("Private Chats:", private_chats)

    private_chat_data = []
    for chat in private_chats:
        other_user_id = chat["user1_id"] if chat["user2_id"] == ObjectId(user_id) else chat["user2_id"]
        other_user = db.users.find_one(
            {"_id": other_user_id},
            {"firstname": 1, "lastname": 1, "image": 1}  # Include profile picture
        )

        # Debug: Print other user data
        print("Other User Data:", other_user)

        if other_user:
            chat_name = f"{other_user['firstname']} {other_user['lastname']}"
            profile_picture = f"/profile_picture/{other_user_id}" if "image" in other_user else "/static/images/default-profile.png"
        else:
            chat_name = "Unknown"
            profile_picture = "/static/images/default-profile.png"

        last_message = db.messages.find_one(
            {"private_chat_id": chat["_id"]},
            {"message": 1, "timestamp": 1},
            sort=[("timestamp", -1)]
        )

        private_chat_data.append({
            "id": str(chat["_id"]),
            "name": chat_name,
            "type": "private",
            "image": profile_picture,  # Ensure correct profile image path
            "last_message": format_last_message(last_message["message"]) if last_message else "No messages yet",
            "timestamp": format_timestamp(last_message["timestamp"]) if last_message else ""
        })

    # Format group chats
    formatted_group_chats = [
        {
            "id": str(chat["_id"]),
            "name": chat["name"],
            "type": "group",
            "image": chat["image"],  # Ensure group image is included
            "last_message": chat["last_message"],
            "timestamp": chat["timestamp"]
        }
        for chat in group_chats
    ]

    # Debug: Print formatted group chats
    print("Formatted Group Chats:", formatted_group_chats)

    # Merge and sort by timestamp
    all_chats = formatted_group_chats + private_chat_data
    all_chats.sort(key=lambda chat: chat["timestamp"] or "1970-01-01T00:00:00Z", reverse=True)

    # Debug: Print all chats
    print("All Chats:", all_chats)

    return all_chats

# -------------------------------------------------------------------------------------

def format_last_message(msg):
    """Detect file URLs and format them properly."""
    if msg is None:
        return "No messages yet"

    # Check if it's a file path (assumes files are stored in /uploads/)
    file_pattern = re.compile(r"^/uploads/[\w.-]+\.(\w+)$")
    match = file_pattern.match(msg)

    if match:
        file_ext = match.group(1).upper()  # Extract file extension
        return f"📁 {file_ext} File"  # Example: "📁 PDF File"

    return msg[:20]  # Truncate normal text messages


def format_timestamp(timestamp):
    """Convert MongoDB timestamp to local time."""
    if not timestamp:
        return ""

    utc_time = timestamp.replace(tzinfo=pytz.utc)
    local_time = utc_time.astimezone(user_timezone)
    return local_time.strftime('%H:%M')


# ------------------------------------------------------------------
@app.route("/chat")
def chats():
    if "user_id" not in session:
        return redirect(url_for("login"))  

    user_id = session["user_id"]
    all_chats = get_user_chats(user_id)

    for chat in all_chats:
        chat["id"] = str(chat["id"])

    return render_template(
        "chat.html", 
        chats=all_chats, 
        firstname=session.get("firstname"), 
        staffid=session.get("staffid"),
        user_id=session.get("user_id") 
        
        )


# ---------------------------------------------------------------------------
@app.route('/chat/<chat_type>/<chat_id>')
def open_chat(chat_type, chat_id):
    """Render the chat page with messages and chat details."""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))  # Ensure user is logged in

    group = None
    private_chat = None
    messages = []

    if chat_type == "group":
        group = get_group_by_id(ObjectId(chat_id))  # Convert to ObjectId
        if not group:
            return "Group not found", 404
        messages = get_messages_for_group(ObjectId(chat_id))
    elif chat_type == "private":
        private_chat = get_private_chat_by_id(ObjectId(chat_id))
        if not private_chat:
            return "Private chat not found", 404
        messages = get_messages_for_private_chat(ObjectId(chat_id))

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

# -----------------------------------------------
@app.route("/get_messages", methods=["GET"])
def get_messages():
    db = get_db_connection()  # Get MongoDB connection
    chat_id = request.args.get("chat_id")
    chat_type = request.args.get("chat_type")

    if not chat_id or chat_type not in ["group", "private"]:
        return jsonify({"error": "Invalid request"}), 400

    try:
        chat_obj_id = ObjectId(chat_id)

        query = {"group_id": chat_obj_id} if chat_type == "group" else {"private_chat_id": chat_obj_id}
        messages_cursor = db.messages.find(query).sort("timestamp", 1)  # Sort ascending

        messages = []
        for msg in messages_cursor:
            user = db.users.find_one({"_id": ObjectId(msg["user_id"])}, {"firstname": 1, "lastname": 1})
            sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown User"

            # Handle both text and files correctly
            message_content = None if msg["message_type"] != "text" else msg["message"]
            file_url = msg["message"] if msg["message_type"] in ["image", "file", "video", "audio"] else None

            messages.append({
                "id": str(msg["_id"]),
                "user_id": str(msg["user_id"]),
                "sender": sender_name,
                "group_id": str(msg["group_id"]) if msg.get("group_id") else None,
                "private_chat_id": str(msg["private_chat_id"]) if msg.get("private_chat_id") else None,
                "message": message_content,
                "file_url": file_url,
                "message_type": msg["message_type"],
                "timestamp": msg["timestamp"].isoformat() if "timestamp" in msg else None
            })

        return jsonify({"messages": messages})

    except Exception as e:
        print(f"❌ ERROR: Fetching messages failed - {e}")
        return jsonify({"error": "Something went wrong"}), 500

# ------------------------------------------------------------------------------------

# @socketio.on("send_message")
# def handle_send_message(data):
#     db = get_db_connection()

#     user_id = data.get("user_id")
#     group_id = data.get("group_id")
#     private_chat_id = data.get("private_chat_id")
#     message = data.get("message")
#     file_path = data.get("file_path")
#     message_type = data.get("message_type", "text")

#     if not group_id and not private_chat_id:
#         print("❌ ERROR: Message must belong to either a group or private chat")
#         return

#     try:
#         message_doc = {
#             "user_id": ObjectId(user_id),
#             "group_id": ObjectId(group_id) if group_id else None,
#             "private_chat_id": ObjectId(private_chat_id) if private_chat_id else None,
#             "message": message if message_type == "text" else None,
#             "message_type": message_type,
#             "timestamp": datetime.utcnow()
#         }

#         # Store file path for non-text messages
#         if message_type in ["image", "file", "video", "audio"]:
#             message_doc["message"] = file_path  # Store file URL in 'message' field

#         message_id = db.messages.insert_one(message_doc).inserted_id
#         print("✅ Message saved to MongoDB:", message_id)

#         # Convert BSON to JSON-friendly format before emitting
#         message_data = {
#             "id": str(message_id),
#             "user_id": str(message_doc["user_id"]),
#             "group_id": str(message_doc["group_id"]) if message_doc["group_id"] else None,
#             "private_chat_id": str(message_doc["private_chat_id"]) if message_doc["private_chat_id"] else None,
#             "message": message_doc["message"],
#             "message_type": message_doc["message_type"],
#             "timestamp": int(message_doc["timestamp"].timestamp() * 1000)  # Convert to milliseconds
#         }

#         # Determine the room
#         room = str(group_id) if group_id else str(private_chat_id)
#         socketio.emit("receive_message", message_data, room=room)
#         print(f"📡 Emitting message to room: {room}")

#     except Exception as e:
#         print(f"❌ Unexpected error: {e}")
# ------------------------------------------------------------------

# @socketio.on("send_message")
# def handle_send_message(data):
#     db = get_db_connection()

#     user_id = data.get("user_id")
#     group_id = data.get("group_id")
#     private_chat_id = data.get("private_chat_id")
#     message = data.get("message")
#     message_type = data.get("message_type", "text")

#     if not user_id or (not group_id and not private_chat_id):
#         print("❌ ERROR: Invalid message request")
#         return

#     try:
#         # Convert IDs to ObjectId
#         message_doc = {
#             "user_id": ObjectId(user_id),
#             "group_id": ObjectId(group_id) if group_id else None,
#             "private_chat_id": ObjectId(private_chat_id) if private_chat_id else None,
#             "message": message,
#             "message_type": message_type,
#             "timestamp": datetime.utcnow()
#         }

#         message_id = db.messages.insert_one(message_doc).inserted_id
#         print("✅ Message saved to MongoDB:", message_id)

#         # Fetch sender's name
#         user = db.users.find_one({"_id": ObjectId(user_id)}, {"firstname": 1, "lastname": 1})
#         sender_name = f"{user['firstname']} {user['lastname']}" if user else "Unknown User"

#         # Construct response message
#         message_data = {
#             "id": str(message_id),
#             "user_id": str(user_id),
#             "sender": sender_name,  # ✅ Include sender name
#             "group_id": str(group_id) if group_id else None,
#             "private_chat_id": str(private_chat_id) if private_chat_id else None,
#             "message": message if message_type == "text" else None,
#             "file_url": message if message_type in ["image", "file", "video", "audio"] else None,  # ✅ Ensure file_url is sent
#             "message_type": message_type,
#             "timestamp": int(message_doc["timestamp"].timestamp() * 1000)
#         }

#         # Emit the message in real-time
#         room = str(group_id) if group_id else str(private_chat_id)
#         socketio.emit("receive_message", message_data, room=room)
#         print(f"📡 Emitting message to room: {room}")

#     except Exception as e:
#         print(f"❌ Unexpected error: {e}")


# working----------
@socketio.on("send_message")
def handle_send_message(data):
    db = get_db_connection()

    user_id = data.get("user_id")
    group_id = data.get("group_id")
    private_chat_id = data.get("private_chat_id")
    message = data.get("message")
    message_type = data.get("message_type", "text")

    if not group_id and not private_chat_id:
        print("❌ ERROR: Message must belong to either a group or private chat")
        return

    try:
        message_doc = {
            "user_id": ObjectId(user_id),
            "group_id": ObjectId(group_id) if group_id else None,
            "private_chat_id": ObjectId(private_chat_id) if private_chat_id else None,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.utcnow()
        }

        message_id = db.messages.insert_one(message_doc).inserted_id
        print("✅ Message saved to MongoDB:", message_id)

        message_data = {
            "id": str(message_id),
            "user_id": str(message_doc["user_id"]),
            "group_id": str(message_doc["group_id"]) if message_doc["group_id"] else None,
            "private_chat_id": str(message_doc["private_chat_id"]) if message_doc["private_chat_id"] else None,
            "message": message_doc["message"],
            "message_type": message_doc["message_type"],
            "timestamp": int(message_doc["timestamp"].timestamp() * 1000)
        }

        room = str(group_id) if group_id else str(private_chat_id)
        socketio.emit("receive_message", message_data, room=room)
        print(f"📡 Emitting message to room: {room}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")



# -----------------------------------------------------------


# # -------------------------------------------------------------------------------------
# @app.route("/get_chat_list")
# def get_chat_list():
#     user_id = session.get("user_id")
#     if not user_id:
#         return jsonify([])

#     user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
#     if not user:
#         return jsonify([])

#     chat_list = []
#     for chat in user.get("groups", []):  # Assuming groups are stored in user doc
#         group = mongo.db.groups.find_one({"_id": ObjectId(chat)})
#         if group:
#             chat_list.append({
#                 "_id": str(group["_id"]),
#                 "name": group["name"],
#                 "type": "group",
#                 "last_message": group.get("last_message", ""),
#                 "timestamp": group.get("timestamp", ""),
#             })

#     return jsonify(chat_list)

@app.route("/get_chat_list")
def get_chat_list():
    if "user_id" not in session:
        return jsonify([])  # Return an empty list if the user is not logged in

    user_id = session["user_id"]
    updated_chats = get_user_chats(user_id)  # Fetch updated chat list

    for chat in updated_chats:
        chat["id"] = str(chat["id"])  # Convert ObjectId to string

    return jsonify(updated_chats)  # Return chat list as JSON


# -------------------------------------------------------------------

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
# # search bar
# @app.route("/search_users")
# def search_users():
#     query = request.args.get("query", "").strip()
#     user_id = session.get("user_id")  # Get logged-in user ID

#     if len(query) < 2:
#         return jsonify([])  # Return empty list if query is too short

#     conn = get_db_connection()
#     cursor = conn.cursor()

#     cursor.execute(
#         "SELECT id, firstname, lastname, staffid FROM users "
#         "WHERE (firstname LIKE ? OR lastname LIKE ? OR staffid LIKE ?) AND id != ?",
#         (f"%{query}%", f"%{query}%", f"%{query}%", user_id)
#     )

#     users = cursor.fetchall()
#     conn.close()

#     # Convert results to a list of dictionaries
#     user_list = [
#         {
#             "id": user["id"],
#             "firstname": user["firstname"],
#             "lastname": user["lastname"],
#             "staffid": user["staffid"],
#         }
#         for user in users
#     ]

#     return jsonify(user_list)

@app.route("/search_users")
def search_users():
    query = request.args.get("query", "").strip()
    user_id = session.get("user_id")  # Get logged-in user ID

    if len(query) < 2:
        return jsonify([])  # Return empty list if query is too short

    try:
        user_object_id = ObjectId(user_id)
    except:
        return jsonify([])  # Return empty list if user_id is invalid

    # Query MongoDB for users matching the search criteria
    users = mongo.db.users.find(
        {
            "$and": [
                {
                    "$or": [
                        {"firstname": {"$regex": query, "$options": "i"}},
                        {"lastname": {"$regex": query, "$options": "i"}},
                        {"staffid": {"$regex": query, "$options": "i"}},
                    ]
                },
                {"_id": {"$ne": user_object_id}},  # Exclude logged-in user
            ]
        },
        {"_id": 1, "firstname": 1, "lastname": 1, "staffid": 1}  # No need to query "image" field
    )

    user_list = [
        {
            "id": str(user["_id"]),
            "firstname": user["firstname"],
            "lastname": user["lastname"],
            "staffid": user["staffid"],
            "image_url": url_for("get_profile_picture", user_id=str(user["_id"])),  # Use profile picture URL
        }
        for user in users
    ]

    return jsonify(user_list)


# @app.route("/search_users")
# def search_users():
#     query = request.args.get("query", "").strip()
#     user_id = session.get("user_id")  # Get logged-in user ID

#     if len(query) < 2:
#         return jsonify([])  # Return empty list if query is too short

#     # Search in firstname, lastname, and staffid
#     users = users_collection.find(
#         {
#             "$and": [
#                 {
#                     "$or": [
#                         {"firstname": {"$regex": query, "$options": "i"}},
#                         {"lastname": {"$regex": query, "$options": "i"}},
#                         {"staffid": {"$regex": query, "$options": "i"}}
#                     ]
#                 },
#                 {"_id": {"$ne": user_id}}  # Exclude the logged-in user
#             ]
#         },
#         {"_id": 1, "firstname": 1, "lastname": 1, "staffid": 1}
#     )

#     # Convert cursor to list of dictionaries
#     user_list = [
#         {
#             "id": str(user["_id"]),  # Convert ObjectId to string
#             "firstname": user["firstname"],
#             "lastname": user["lastname"],
#             "staffid": user["staffid"],
#         }
#         for user in users
#     ]

#     return jsonify(user_list)



# ----------------------------------------------------------------------


# @app.route('/start_private_chat', methods=['POST'])
# def start_private_chat():
#     user1_id = session.get("user_id")  # Logged-in user
#     user2_id = request.json.get("user_id")  # Selected user

#     if not user1_id or not user2_id:
#         return jsonify({"error": "Invalid users"}), 400

#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Check if chat already exists
#     cursor.execute(
#         "SELECT id FROM private_chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
#         (user1_id, user2_id, user2_id, user1_id),
#     )
#     chat = cursor.fetchone()

#     if chat:
#         chat_id = chat["id"]
#     else:
#         # Create new private chat
#         cursor.execute(
#             "INSERT INTO private_chats (user1_id, user2_id) VALUES (?, ?)",
#             (user1_id, user2_id),
#         )
#         conn.commit()
#         chat_id = cursor.lastrowid

#     conn.close()

#     return jsonify({"chat_id": chat_id, "user_id": user2_id})

@app.route("/start_private_chat", methods=["POST"])
def start_private_chat():
    data = request.get_json()
    user_id = session.get("user_id")  # Logged-in user
    other_user_id = data.get("user_id")

    if not user_id or not ObjectId.is_valid(user_id) or not ObjectId.is_valid(other_user_id):
        return jsonify({"success": False, "error": "Invalid user ID"}), 400

    db = get_db_connection()

    # Check if a private chat already exists
    existing_chat = db.private_chats.find_one({
        "$or": [
            {"user1_id": ObjectId(user_id), "user2_id": ObjectId(other_user_id)},
            {"user1_id": ObjectId(other_user_id), "user2_id": ObjectId(user_id)}
        ]
    })

    if not existing_chat:
        # Create new chat if it does not exist
        db.private_chats.insert_one({
            "user1_id": ObjectId(user_id),
            "user2_id": ObjectId(other_user_id),
            "messages": []
        })

    # Retrieve the user's profile image
    user_data = db.users.find_one({"_id": ObjectId(other_user_id)}, {"firstname": 1, "lastname": 1, "image": 1})
    if not user_data:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Get the image URL
    image_url = url_for("get_profile_picture", user_id=str(user_data["_id"])) if user_data.get("image") else None

    return jsonify({"success": True, "image_url": image_url})


# @app.route("/start_private_chat", methods=["POST"])
# def start_private_chat():
#     data = request.json
#     user1_id = session.get("user_id")  # Logged-in user
#     user2_id = data.get("user_id")  # Selected user

#     if not user1_id or not user2_id:
#         return jsonify({"error": "Invalid request"}), 400

#     user1_id = ObjectId(user1_id)
#     user2_id = ObjectId(user2_id)

#     # Check if a private chat already exists
#     existing_chat = db.private_chats.find_one({
#         "$or": [
#             {"user1_id": user1_id, "user2_id": user2_id},
#             {"user1_id": user2_id, "user2_id": user1_id}
#         ]
#     })

#     if not existing_chat:
#         # Create a new private chat
#         chat_id = db.private_chats.insert_one({
#             "user1_id": user1_id,
#             "user2_id": user2_id,
#             "messages": []
#         }).inserted_id
#     else:
#         chat_id = existing_chat["_id"]

#     # Fetch the updated chat list
#     chat_list = list(db.private_chats.find(
#         {"$or": [{"user1_id": user1_id}, {"user2_id": user1_id}]}
#     ))

#     chat_list_response = []
#     for chat in chat_list:
#         other_user_id = chat["user2_id"] if chat["user1_id"] == user1_id else chat["user1_id"]
#         other_user = db.users.find_one({"_id": other_user_id}, {"firstname": 1, "lastname": 1, "staffid": 1})
        
#         if other_user:
#             chat_list_response.append({
#                 "chat_id": str(chat["_id"]),
#                 "user_id": str(other_user["_id"]),
#                 "name": f"{other_user['firstname']} {other_user['lastname']}",
#                 "staffid": other_user["staffid"]
#             })

#     return jsonify({"chat_id": str(chat_id), "chat_list": chat_list_response})


# ---------------------------------------------------------------------------

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
        'group_id': session.get('group_id'),
        'private_chat_id': session.get('private_chat_id')
    })



# App Login Page Route 
@app.route('/login')
def login():
    return render_template('login.html')



@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    session.pop('firstname', None)  # Remove firstname from session
    session.pop('staffid', None)  # Remove staffid from session (if stored)
    
    session.clear()  # Clear entire session
    return redirect(url_for('login'))






# Protected Route (Only accessible when logged in)
@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template("profile.html", firstname=session.get("firstname"), staffid=session.get("staffid"))





@app.route('/debug_session')
def debug_session():
    return jsonify(dict(session))  # ✅ View session contents








# Start Application
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)