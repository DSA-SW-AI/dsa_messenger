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
# BLUEPRINTS NAME
# Create a blueprint for the logout routes
logout_bp = Blueprint('logout', __name__)

# ========================== LOGOUT =================================

@logout_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    session.pop('firstname', None)  # Remove firstname from session
    session.pop('staffid', None)  # Remove staffid from session (if stored)
    
    session.clear()  # Clear entire session
    return redirect(url_for('user_reg_and_login.login'))

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# ========================== GET SESSION DATA =================================
@logout_bp.route('/get_session_data', methods=['GET'])
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

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx



# ========================== DEBUG SESSION =================================

@logout_bp.route('/debug_session')
def debug_session():
    return jsonify(dict(session))  # ✅ View session contents

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

