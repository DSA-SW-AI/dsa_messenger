from datetime import datetime, timedelta
from pymongo import MongoClient
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


# ======================= DATABASE CONNECTION ======================================================
# Set up database and GridFs
# This function establishes a connection to the MongoDB database and returns the database object.
# It uses the MongoClient to connect to the database and specifies the database name.

def get_db_connection():
    MONGO_URI = "mongodb://localhost:27017/chatDatabase"
    mongo_client = MongoClient(MONGO_URI)
    # Set up database and GridFS
    db = mongo_client["chatDatabase"]
    return db

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= ALLOWED FILES =======================================================
# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mp3", "pdf", "docx"}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= TIMESTAMP ===========================================================
# Timestamp
# This function formats a timestamp to a more readable format.
def format_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= GET GROUP BY ID ======================================================
# ✅ Function to get a group by ID
# This function retrieves a group from the database based on the group_id.

def get_group_by_id(group_id):
    db = get_db_connection()
    group = db.groups.find_one({"_id": ObjectId(group_id)}, {"_id": 1, "name": 1})
    if group:
        group["id"] = str(group["_id"])  # Convert ObjectId to string for JSON compatibility
        del group["_id"]
    return group  # Returns a dictionary or None

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =============================== GET MESSAGES FOR GROUP ============================================
# ✅ Function to get messages for a group
# This function retrieves messages for a group based on the group_id.

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
    
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================= GET MESSAGES FOR PRIVATE CHAT ============================================
# ✅ Function to get messages for a private chat
# This function retrieves messages for a private chat based on the private_chat_id.

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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ========================= GET PRIVATE CHAT BY ID ======================================================
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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================================= GET USER CHAT ================================================
# # Define the user's timezone

user_timezone = pytz.timezone('Africa/Lagos')  # Update with the correct timezone


def get_user_chats(user_id):
    db = get_db_connection()

    user = db.users.find_one({"_id": ObjectId(user_id)}, {"groups": 1})
    if not user:
        return []

    # Get user's groups, excluding deleted ones
    group_chats = list(db.groups.find(
    {"_id": {"$in": user["groups"]}, "deleted": {"$ne": True}},  # Exclude deleted chats
    {"_id": 1, "name": 1, "image": 1}
))


    for group in group_chats:
        last_message = db.messages.find_one(
            {"group_id": group["_id"]},
            {"message": 1, "timestamp": 1},
            sort=[("timestamp", -1)]
        )
        group["type"] = "group"
        group["image"] = group.get("image", "")
        group["last_message"] = format_last_message(last_message["message"]) if last_message else "No messages yet"
        group["timestamp"] = format_timestamp(last_message["timestamp"]) if last_message else ""

    # Get private chats, excluding deleted ones
    private_chats = list(db.private_chats.find(
    {
        "$or": [{"user1_id": ObjectId(user_id)}, {"user2_id": ObjectId(user_id)}],
        "deleted": {"$ne": True}  # Exclude deleted chats
    }
))


    private_chat_data = []
    for chat in private_chats:
        other_user_id = chat["user1_id"] if chat["user2_id"] == ObjectId(user_id) else chat["user2_id"]
        other_user = db.users.find_one(
            {"_id": other_user_id},
            {"firstname": 1, "lastname": 1, "image": 1}
        )

        chat_name = f"{other_user['firstname']} {other_user['lastname']}" if other_user else "Unknown"
        profile_picture = f"/profile_picture/{other_user_id}" if other_user and "image" in other_user else "/static/images/default-profile.png"

        last_message = db.messages.find_one(
            {"private_chat_id": chat["_id"]},
            {"message": 1, "timestamp": 1},
            sort=[("timestamp", -1)]
        )

        private_chat_data.append({
            "id": str(chat["_id"]),
            "name": chat_name,
            "type": "private",
            "image": profile_picture,
            "last_message": format_last_message(last_message["message"]) if last_message else "No messages yet",
            "timestamp": format_timestamp(last_message["timestamp"]) if last_message else ""
        })

    # Format and sort chats
    formatted_group_chats = [
        {
            "id": str(chat["_id"]),
            "name": chat["name"],
            "type": "group",
            "image": chat["image"],
            "last_message": chat["last_message"],
            "timestamp": chat["timestamp"]
        }
        for chat in group_chats
    ]

    all_chats = formatted_group_chats + private_chat_data
    all_chats.sort(key=lambda chat: chat["timestamp"] or "1970-01-01T00:00:00Z", reverse=True)

    return all_chats

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================== FORMAT LAST MESSAGES =================================================

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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==================================== FORMAT TIMESTAMP ================================================

def format_timestamp(timestamp):
    """Format timestamps like WhatsApp: time for today, 'Yesterday' for yesterday, and date for older messages."""
    if not timestamp:
        return ""

    utc_time = timestamp.replace(tzinfo=pytz.utc)
    local_time = utc_time.astimezone(user_timezone)

    now = datetime.now(user_timezone).date()
    msg_date = local_time.date()

    if msg_date == now:
        return local_time.strftime('%I:%M %p')  # Show time (e.g., 10:30 AM)
    elif msg_date == now - timedelta(days=1):
        return "Yesterday"
    else:
        return local_time.strftime('%d-%b-%y')  # Show date (e.g., 22-Mar-25)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ======================================= GET CHATS ====================================================

def get_chats():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    db = get_db_connection()

    # Fetch user's private chats
    private_chats = list(db.private_chats.find({
        "$or": [{"user1_id": ObjectId(user_id)}, {"user2_id": ObjectId(user_id)}]
    }))

    private_chat_list = []
    for chat in private_chats:
        other_user_id = chat["user1_id"] if str(chat["user2_id"]) == user_id else chat["user2_id"]
        other_user = db.users.find_one({"_id": other_user_id}, {"firstname": 1, "lastname": 1, "image": 1})

        if other_user:
            private_chat_list.append({
                "chat_id": str(chat["_id"]),
                "chat_type": "private",
                "name": f"{other_user.get('firstname', 'Unknown')} {other_user.get('lastname', '')}",
                "image_url": url_for("get_profile_picture", user_id=str(other_user["_id"])) if other_user.get("image") else None,
                "unread_count": 0  # Update this logic based on unread messages
            })

    # Fetch user's group chats
    user_groups = db.groups.find({"members": ObjectId(user_id)})
    group_chat_list = [{
        "chat_id": str(group["_id"]),
        "chat_type": "group",
        "name": group["name"],
        "image_url": "/static/group-avatar.png",
        "unread_count": 0  # Update based on unread messages
    } for group in user_groups]

    return jsonify({"success": True, "chats": private_chat_list + group_chat_list})

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =================================== GET UNREAD COUNT ==================================================

def get_unread_count(user_id):
    db = get_db_connection()

    unread_private = {}
    unread_group = {}

    # Private Chats: Count unread messages from others
    private_chats = db.private_chats.find({
        "$or": [{"user1_id": ObjectId(user_id)}, {"user2_id": ObjectId(user_id)}]
    })
    
    for chat in private_chats:
        unread_count = db.messages.count_documents({
            "private_chat_id": chat["_id"],
            "sender_id": {"$ne": ObjectId(user_id)},  # Others' messages
            "read_by": {"$nin": [ObjectId(user_id)]}   # Not read by current user
        })
        unread_private[str(chat["_id"])] = unread_count

    # Group Chats: Count unread messages (regardless of sender)
    user_groups = db.users.find_one(
        {"_id": ObjectId(user_id)}, 
        {"groups": 1}
    )
    
    if user_groups and "groups" in user_groups:
        for group_id in user_groups["groups"]:
            unread_count = db.messages.count_documents({
                "group_id": group_id,
                "read_by": {"$nin": [ObjectId(user_id)]}  # Not read by current user
            })
            unread_group[str(group_id)] = unread_count

    print("Unread Count - Private:", unread_private)  # Debugging output
    print("Unread Count - Group:", unread_group)  # Debugging output

    return {"private": unread_private, "group": unread_group}

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

