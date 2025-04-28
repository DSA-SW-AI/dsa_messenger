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

user_auth_bp = Blueprint('user_reg_and_login', __name__)

# =================================== REGISTER APP ROUTE ===================================
# App Register Page Route

@user_auth_bp.route('/register')
def register():
    # Fetch all groups **except** the "Civillian Staff" group
    groups = list(db.groups.find({"name": {"$ne": "CIVILLIAN STAFF"}}, {"_id": 1, "name": 1}))

    questions_collection = db['security_questions']
    questions = questions_collection.find()
    questions_list = [q['question'] for q in questions]

    return render_template("register.html", groups=groups, questions=questions_list)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ====================================== REGISTRATION FORM SUBMIT ============================

# Registration Form Route
@user_auth_bp.route('/submit_register', methods=['POST'])
def submit_register():
    try:
        staffid = request.form.get('staffid')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        directorate = request.form.get('group_id')
        password = request.form.get('password')
        con_password = request.form.get('con_password')
        profile_picture = request.files.get('profile_picture')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        if not all([staffid, fname, lname, directorate, password, con_password, profile_picture, security_question, security_answer]):
            return jsonify({"success": False, "message": "All fields are required"}), 400

        if password != con_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)
        hashed_answer = generate_password_hash(security_answer)

        # Check if the user already exists
        existing_user = db.users.find_one({"staffid": staffid})
        if existing_user:
            return jsonify({"success": False, "message": "User with this Staff ID already exists"}), 400



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
            "groups": [ObjectId(directorate), civillian_group["_id"]],
            "security_question": security_question,
            "security_answer": hashed_answer,
        }
        db.users.insert_one(user_data)
        return jsonify({"success": True, "message": "Registration successful!"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================== LOGIN APP ROUTE ===================================

# App login Verifcation Route
@user_auth_bp.route('/submit_login', methods=['POST'])
def submit_login():
    data = request.json
    staffid = data.get("staffid")
    password = data.get("password")
    remember_me = data.get("remember", False)

    user = users.find_one({"staffid": staffid})

    if user and "password" in user:
        stored_password = user["password"]

        # Use Werkzeug's check_password_hash instead of bcrypt
        if check_password_hash(stored_password, password):
            session['user_id'] = str(user["_id"])
            session['firstname'] = user['firstname']
            session['staffid'] = user['staffid']


            if remember_me:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)

                
            return jsonify({"success": True, "redirect": "/chat"})
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    else:
        return jsonify({"success": False, "error": "User not found"}), 404

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ================================== LOGIN APP ROUTE ===================================

# App Login Page Route 
@user_auth_bp.route('/login')
def login():
    return render_template('login.html')

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx