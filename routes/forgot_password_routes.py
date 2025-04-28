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

forgot_password_bp = Blueprint('password_reset', __name__)


# ==========================FORGOT PASSWORD =================================

@forgot_password_bp.route('/forgot_password')
def forgot_password():
        
    return render_template("forgot_password.html")

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ========================== RESET PASSWORD ==================================
@forgot_password_bp.route('/reset_password', methods=['GET'])
def reset_password():
    staffid = request.args.get('staffid')

    # Optional: verify staffid exists before rendering
    user = db.users.find_one({"staffid": staffid})
    if not user:
        flash("Invalid request. User not found.", "error")
        return redirect('/forgot_password')

    return render_template('reset_password.html', staffid=staffid)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =========================== RESET PASSWORD POST =========================
@forgot_password_bp.route('/reset_password', methods=['POST'])
def reset_password_post():
    try:

        data = request.get_json()

        print("Received data:", data)

        staffid = data.get('staffid')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            return jsonify({"success": False, "error": "Passwords do not match"}), 400

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update the user's password in the database
        result = db.users.update_one({"staffid": staffid}, {"$set": {"password": hashed_password}})

        if result.matched_count > 0:
            return jsonify({"success": True, "message": "Password updated successfully", "redirect": "/login"}), 200
        else:
            return jsonify({"success": False, "error": "Password not updated or changed"}), 404

    except Exception as e:
        return jsonify({ "success": False, "error": str(e)}), 500

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ====================== GET SECURITY QUESTION ===============================================

@forgot_password_bp.route('/get_security_questions', methods=['GET'])
def get_security_questions():
    questions = questions_collection.find()  # Fetch all security questions
    questions_list = [q['question'] for q in questions]  # Extract the 'question' field
    return render_template('register.html', questions=questions_list)

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

@forgot_password_bp.route('/get_security_question', methods=['POST'])
def get_security_question():
    try:
        staffid = request.form.get('staffid')

        # Find the user by staff ID
        user = db.users.find_one({"staffid": staffid})
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        # Return the security question
        return jsonify({"success": True, "security_question": user["security_question"]}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@forgot_password_bp.route('/verify_security_answer', methods=['POST'])
def verify_security_answer():
    try:
        staffid = request.form.get('staffid')
        security_answer = request.form.get('security_answer')

        # Find the user by staff ID
        user = db.users.find_one({"staffid": staffid})
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        # Verify the security answer
        if check_password_hash(user['security_answer'], security_answer):
            # Security answer matches, allow user to reset password
            return jsonify({"success": True, "message": "Answer correct. Proceed to reset password."}), 200
        else:
            return jsonify({"success": False, "error": "Incorrect security answer"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx