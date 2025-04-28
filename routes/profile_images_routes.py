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
profile_pictures_bp = Blueprint('profile_images', __name__)


# ====================== FILE UPLOAD =======================================================

@profile_pictures_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# ====================== FILE UPLOAD HANDLER ==================================================

@profile_pictures_bp.route("/upload", methods=["POST"])
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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx



# ============================= GET ALL GROUP PROFILE IMAGE ==================================
@profile_pictures_bp.route('/group_image/<group_id>')
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
    
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================= GET STATIC FILE FROM STATIC FOLDER ===========================

# @profile_pictures_bp.route('/static/<path:filename>')
# def serve_static(filename):
#     return send_from_directory('static', filename)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =================================== GET USER PROFILE PICTURE ===============================
@profile_pictures_bp.route('/profile_picture/<user_id>')
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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx