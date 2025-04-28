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
# Create a blueprint for the profile images routes
search_users_bp = Blueprint('search', __name__)

# ======================== SEARCH USERS ====================================

@search_users_bp.route("/search_users")
def search_users():
    query = request.args.get("query", "").strip()
    user_id = session.get("user_id")  # Get logged-in user ID

    if not user_id:
        return jsonify([])

    if len(query) < 2:
        return jsonify([])

    try:
        user_object_id = ObjectId(user_id)
    except InvalidId:
        return jsonify([])

    users = db.users.find(
        {
            "$or": [
                {"firstname": {"$regex": query, "$options": "i"}},
                {"lastname": {"$regex": query, "$options": "i"}},
                {"staffid": {"$regex": query, "$options": "i"}},
            ],
            "_id": {"$ne": user_object_id}
        },
        {"_id": 1, "firstname": 1, "lastname": 1, "staffid": 1}
    )

    user_list = [
        {
            "id": str(user["_id"]),
            "firstname": user.get("firstname", ""),
            "lastname": user.get("lastname", ""),
            "staffid": user.get("staffid", ""),
            "image_url": url_for("profile_images.get_profile_picture", user_id=str(user["_id"])),
        }
        for user in users
    ]

    return jsonify(user_list)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx