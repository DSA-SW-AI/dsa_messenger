from flask import Flask, Blueprint, current_app,  request, jsonify, render_template, make_response, redirect, Request, url_for, session, send_from_directory, Response, flash
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
from utils.functions import get_db_connection
from bson import ObjectId
from bson.errors import InvalidId






# ======================= DATABASE CONNECTION ======================================================
MONGO_URI = "mongodb://localhost:27017/chatDatabase"

# Simple local client
mongo_client = MongoClient(MONGO_URI)

# Set up database and GridFS
db = mongo_client["chatDatabase"]
fs = gridfs.GridFS(db)  # GridFS instance

# Set up Flask-PyMongo
  

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
# BLUEPRINTS NAME
private_chats_bp = Blueprint('private_chat', __name__)



# ================================= START PRIVATE CHAT FROM SEARCH RESULT ============================================

@private_chats_bp.route("/start_private_chat", methods=["POST"])
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

    if existing_chat:
        chat_id = str(existing_chat["_id"])
    else:
        # Create new chat if it does not exist
        new_chat = db.private_chats.insert_one({
            "user1_id": ObjectId(user_id),
            "user2_id": ObjectId(other_user_id),
            "messages": []
        })
        chat_id = str(new_chat.inserted_id)

    # Retrieve the other user's details
    user_data = db.users.find_one({"_id": ObjectId(other_user_id)}, {"firstname": 1, "lastname": 1, "image": 1})
    if not user_data:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Get the image URL
    image_url = url_for("profile_images.get_profile_picture", user_id=str(user_data["_id"])) if user_data.get("image") else None

    return jsonify({
        "success": True,
        "chat_id": chat_id,
        "image_url": image_url
    })

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx