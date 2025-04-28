from flask import Flask, request, jsonify, render_template, make_response, redirect, Request, url_for, session, send_from_directory, Response, flash
from pymongo import DESCENDING, MongoClient
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
from utils.functions import get_db_connection, get_chats, get_unread_count, get_user_chats, get_messages_for_group, get_messages_for_private_chat,get_private_chat_by_id, get_group_by_id, format_last_message, format_timestamp, allowed_file

# BLUEPRINT IMPORTS
from routes.auth_routes import user_auth_bp
from routes.forgot_password_routes import forgot_password_bp
from routes.logout_routes import logout_bp
from routes.profile_images_routes import profile_pictures_bp
from routes.search_user_routes import search_users_bp
from routes.private_chat_routes import private_chats_bp
from routes.get_messages_rooutes import get_messages_bp
from routes.profile_routes import profile_bp





# ======================= FLASK APP SETUP =============================================================

app = Flask(__name__)
app.secret_key = 'thiskeyissupposedtobeprivateandonlyknowbytheadmin'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, supports_credentials=True)
app.permanent_session_lifetime = timedelta(hours=2)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= DATABASE CONNECTION =========================================================
MONGO_URI = "mongodb://localhost:27017/chatDatabase"

# Simple local client
mongo_client = MongoClient(MONGO_URI)

# Set up database and GridFS
db = mongo_client["chatDatabase"]
fs = gridfs.GridFS(db)  # GridFS instance

# Set up Flask-PyMongo
app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)  

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= DATABASE COLLECTIONS ===============================================
# Define collections
users = db["users"]
users_collection = db["users"]
groups_collection = db["groups"]
user_groups_collection = db["user_groups"]
private_chats_collection = db["private_chats"]
messages_collection = db["messages"]
questions_collection = db['security_questions']

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =============================== APP BLUEPRINT ROUTES =======================================

# REGISTER USER AUTHENTICATION ROUTES
app.register_blueprint(user_auth_bp)


# REGISTER FORGOT PASSWORD ROUTES
app.register_blueprint(forgot_password_bp)


# REGISTER LOGOUT ROUTES
app.register_blueprint(logout_bp)


# REGISTER PROFILE PICTURE ROUTES
app.register_blueprint(profile_pictures_bp)


# REGISTER SEARCH USER ROUTES
app.register_blueprint(search_users_bp)


# PRIVATE CHAT ROUTES
app.register_blueprint(private_chats_bp)


# GET ALL MESSAGES ROUTES
app.register_blueprint(get_messages_bp)


# GET ALL MESSAGES ROUTES
app.register_blueprint(profile_bp)


# ============================== HOMEPAGE APP ROUTE ==========================================
# App HomePage Route
@app.route('/')
def index():
    return render_template("home.html")

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ====================== ALLOWED FILES =======================================================

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ================================= GET CHAT LIST ==========================================

@app.route("/chat")
def chats():
    if "user_id" not in session:
        return redirect(url_for("login"))  

    user_id = session["user_id"]
    all_chats = get_user_chats(user_id)

    # Get unread counts for all chats
    unread_count_data = get_unread_count(user_id)

    for chat in all_chats:
        chat_id = str(chat["id"])
        if chat["type"] == "group":  # Check based on "type"
            chat["unread_count"] = unread_count_data["group"].get(chat_id, 0)
        else:
            chat["unread_count"] = unread_count_data["private"].get(chat_id, 0)

        print(f"Chat: {chat['name']} (Type: {chat['type']}), Unread: {chat['unread_count']}")  # Debugging Output



    return render_template(
        "chat.html", 
        chats=all_chats, 
        firstname=session.get("firstname"), 
        staffid=session.get("staffid"),
        user_id=session.get("user_id")
    )
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =========================== GET SELECTED CHAT FROM THE CHAT LIST =====================================
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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================== SOCKET IO MESSAGE SEND ================================================
# This event is triggered when a user sends a message.

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
        read_by = [ObjectId(user_id)]
        delivered_to = []

        if group_id:
            group = db.groups.find_one({"_id": ObjectId(group_id)})
            if group:
                # Exclude sender from delivery list
                delivered_to = [ObjectId(uid) for uid in group.get("members", []) if str(uid) != user_id]

        message_doc = {
            "user_id": ObjectId(user_id),
            "group_id": ObjectId(group_id) if group_id else None,
            "private_chat_id": ObjectId(private_chat_id) if private_chat_id else None,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.utcnow(),
            "read_by": read_by,
            "delivered_to": [],
            "status": "sent"
        }

        message_id = db.messages.insert_one(message_doc).inserted_id

        message_data = {
            "id": str(message_id),
            "user_id": str(message_doc["user_id"]),
            "group_id": str(message_doc["group_id"]) if group_id else None,
            "private_chat_id": str(message_doc["private_chat_id"]) if private_chat_id else None,
            "message": message_doc["message"],
            "message_type": message_doc["message_type"],
            "timestamp": int(message_doc["timestamp"].timestamp() * 1000),
            "status": "sent",
            "read_by": [str(uid) for uid in message_doc["read_by"]],
            "delivered_to": [str(uid) for uid in message_doc["delivered_to"]]
        }

        room = str(group_id) if group_id else str(private_chat_id)
        socketio.emit("receive_message", message_data, room=room)
        print(f"📡 Message sent to {room}")

    except Exception as e:
        print(f"❌ Error sending message: {e}")

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ================ JOINING ROOMS FOR GROUP AND PRIVATE CHATS ===========================================
# This allows users to join specific rooms for group and private chats

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
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ================================UNREAD MESSAGE COUNT==================================================

@socketio.on("mark_messages_as_read")
def mark_messages_as_read(data):
    db = get_db_connection()

    chat_id = data.get("chat_id")
    chat_type = data.get("chat_type")
    user_id = data.get("user_id")

    if not chat_id or not chat_type or not user_id:
        return

    try:
        filter_query = {}
        update_query = {
            "$addToSet": {"read_by": ObjectId(user_id)},
            "$set": {"status": "read"}
        }

        if chat_type == "group":
            filter_query = {
                "group_id": ObjectId(chat_id),
                "read_by": {"$ne": ObjectId(user_id)}
            }
        else:
            filter_query = {
                "private_chat_id": ObjectId(chat_id),
                "sender_id": {"$ne": ObjectId(user_id)},
                "read_by": {"$ne": ObjectId(user_id)}
            }

        updated_count = db.messages.update_many(filter_query, update_query).modified_count

        # Notify sender and possibly other users that messages were read
        socketio.emit("message_status_update", {
            "chat_id": chat_id,
            "user_id": user_id,
            "status": "read"
        }, room=str(chat_id))

        # Optional: direct update back to reader’s client
        socketio.emit("messages_marked_as_read", {
            "chat_id": chat_id,
            "chat_type": chat_type,
            "updated_count": updated_count
        }, room=str(user_id))

    except Exception as e:
        print(f"❌ Error marking messages as read: {e}")

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================== SOCKET IO MESSAGE DELIVERED ===========================================
# This event is triggered when a message is delivered to the recipient.

@socketio.on("message_delivered")
def handle_message_delivered(data):
    db = get_db_connection()
    message_id = data.get("message_id")
    recipient_id = data.get("user_id")

    try:
        # Step 1: Update the delivered_to and status
        db.messages.update_one(
            {"_id": ObjectId(message_id)},
            {
                "$addToSet": {"delivered_to": ObjectId(recipient_id)},
                "$set": {"status": "delivered"}
            }
        )

        # Step 2: Fetch the message to get sender_id
        message = db.messages.find_one({"_id": ObjectId(message_id)})
        sender_id = str(message["user_id"])

        # Step 3: Notify the **sender**, not the recipient
        socketio.emit("message_status_update", {
            "message_id": message_id,
            "status": "delivered"
        }, room=sender_id)
        print(f"Emitting message status update: {message_id}, status: delivered")

    except Exception as e:
        print(f"❌ Delivery update failed: {e}")
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================== SOCKET IO MESSAGE READ ================================================
# This event is triggered when a message is read by the recipient.

@socketio.on("message_read")
def handle_message_read(data):
    db = get_db_connection()
    message_id = data.get("message_id")
    reader_id = data.get("user_id")

    try:
        # Update read_by and status
        result = db.messages.update_one(
            {"_id": ObjectId(message_id)},
            {
                "$addToSet": {"read_by": ObjectId(reader_id)},
                "$set": {"status": "read"}
            }
        )

        if result.modified_count > 0:
            # Fetch the message to get sender_id
            message = db.messages.find_one({"_id": ObjectId(message_id)})
            sender_id = str(message["user_id"])

            # Notify the sender
            socketio.emit("message_status_update", {
                "message_id": message_id,
                "status": "read"
            }, room=sender_id)
            print(f"Emitting message status update: {message_id}, status: read")

    except Exception as e:
        print(f"❌ Read update failed: {e}")

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ========================= DELETE CHAT ================================================================
# Delete a chat (either private or group)

@app.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat(chat_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    user_id = session["user_id"]
    db = get_db_connection()

    chat = db.private_chats.find_one({"_id": ObjectId(chat_id)})
    if chat:
        # If it's a private chat, mark it as deleted
        db.private_chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"deleted": True}})
        return jsonify({"success": True, "message": "Private chat deleted."})

    group = db.groups.find_one({"_id": ObjectId(chat_id)})
    if group:
        # If it's a group chat, remove the user from the group
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"groups": ObjectId(chat_id)}}  # Remove user from group
        )
        return jsonify({"success": True, "message": "Removed from group chat."})

    return jsonify({"success": False, "error": "Chat not found"}), 404

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

























# Start Application
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)