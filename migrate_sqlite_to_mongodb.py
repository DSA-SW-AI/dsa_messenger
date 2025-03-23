from flask import Flask, request, jsonify, render_template, redirect, Request, url_for, session, send_from_directory
from flask_login import LoginManager, login_required, logout_user
from pymongo import MongoClient
import certifi
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import pytz
from bson.objectid import ObjectId
# from db import save_user, users_collections, get_user
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os
import sqlite3
import re
import gridfs




# Connect to SQLite
sqlite_conn = sqlite3.connect("chatdatabase.db")
sqlite_cursor = sqlite_conn.cursor()



# Connect to MongoDB with GridFS
mongo_client = MongoClient("mongodb+srv://udofiaubong10:qAWzNlJT6x2vSCdb@dsamessenger.tqp9u.mongodb.net", tlsCAFile=certifi.where())
mongo_db = mongo_client["chatDatabase"]
fs = gridfs.GridFS(mongo_db)



# Migrate Users
sqlite_cursor.execute("SELECT id, staffid, firstname, lastname, directorate, password, timestamp FROM users")
users = sqlite_cursor.fetchall()

for user in users:
    user_id, staffid, firstname, lastname, directorate, password, timestamp = user

    # Upload latest profile image to GridFS (overwrites previous one)
    image_id = None
    image_path = f"uploads/{staffid}.jpg"  # Adjust path as needed

    try:
        with open(image_path, "rb") as image_file:
            image_id = fs.put(image_file, filename=f"{staffid}.jpg")
    except FileNotFoundError:
        print(f"⚠️ No profile image found for {staffid}, skipping...")

    # Fetch groups the user belongs to
    sqlite_cursor.execute("SELECT group_id FROM user_groups WHERE user_id = ?", (user_id,))
    group_ids = [ObjectId(str(gid[0])) for gid in sqlite_cursor.fetchall()]

    mongo_db.users.insert_one({
        "_id": ObjectId(str(user_id)),  # Preserve original ID mapping
        "staffid": staffid,
        "firstname": firstname,
        "lastname": lastname,
        "directorate": directorate,
        "password": password,
        "timestamp": timestamp,
        "image_id": str(image_id) if image_id else None,  # Store GridFS image ID
        "groups": group_ids  # Store groups as an array
    })

print("✅ Users migrated successfully!")

# Migrate Groups
sqlite_cursor.execute("SELECT id, name, timestamp FROM groups")
groups = sqlite_cursor.fetchall()

for group in groups:
    group_id, name, timestamp = group
    mongo_db.groups.insert_one({
        "_id": ObjectId(str(group_id)),
        "name": name,
        "timestamp": timestamp
    })

print("✅ Groups migrated successfully!")

# Migrate Messages
sqlite_cursor.execute("SELECT id, user_id, group_id, private_chat_id, message, message_type, timestamp FROM messages")
messages = sqlite_cursor.fetchall()

for message in messages:
    msg_id, user_id, group_id, private_chat_id, msg_text, message_type, timestamp = message

    file_id = None
    if message_type in ["image", "file", "audio", "video"]:
        file_path = f"uploads/{msg_text}"  # Assuming filename is stored in `message` column
        try:
            with open(file_path, "rb") as file_data:
                file_id = fs.put(file_data, filename=msg_text)  # Store in GridFS
        except FileNotFoundError:
            print(f"⚠️ File {msg_text} not found, skipping...")

    mongo_db.messages.insert_one({
        "_id": ObjectId(str(msg_id)),
        "user_id": ObjectId(str(user_id)),
        "group_id": ObjectId(str(group_id)) if group_id else None,
        "private_chat_id": ObjectId(str(private_chat_id)) if private_chat_id else None,
        "message": msg_text if message_type == "text" else None,  # Store text normally
        "file_id": str(file_id) if file_id else None,  # Store GridFS file reference
        "message_type": message_type,
        "timestamp": timestamp
    })

print("✅ Messages migrated successfully!")

# Migrate Private Chats
sqlite_cursor.execute("SELECT id, user1_id, user2_id FROM private_chats")
private_chats = sqlite_cursor.fetchall()

for chat in private_chats:
    chat_id, user1_id, user2_id = chat
    mongo_db.private_chats.insert_one({
        "_id": ObjectId(str(chat_id)),
        "user1_id": ObjectId(str(user1_id)),
        "user2_id": ObjectId(str(user2_id))
    })

print("✅ Private chats migrated successfully!")

# Close connections
sqlite_conn.close()
mongo_client.close()