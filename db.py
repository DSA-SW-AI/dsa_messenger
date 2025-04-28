from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import certifi
from datetime import datetime
import pytz
import gridfs
from bson.objectid import ObjectId
import sqlite3
import os



# MongoDB connection string
mongo_client = "mongodb://localhost:27017/chatDatabase"

try:
    # Connect to MongoDB with SSL certification
    client = MongoClient(mongo_client)  # Use MongoClient correctly

    # Get the database
    chat_db = client.get_database("chatDatabase")

    # Check if connection is successful by listing collections
    collections = chat_db.list_collection_names()

    print("✅ Successfully connected to MongoDB!")
    print("Collections in 'chatDatabase':", collections)
except Exception as e:
    print("❌ Error connecting to MongoDB:", e)





# =============================================================================

from pymongo import MongoClient

# MongoDB connection string
mongo_client = "mongodb://localhost:27017/chatDatabase"
chat_db = client.get_database("chatDatabase")
# collection = chat_db["security_questions"]

# List of security questions
# questions = [
#     "What was the name of your first pet?",
#     "What is the name of the street you grew up on?",
#     "What was the model of your first car?",
#     "What was your childhood nickname?",
#     "What school did you attend for sixth grade?",
#     "What was the name of your elementary school?",
#     "What is your mother’s maiden name?",
#     "What is the name of your oldest cousin?",
#     "What is your father’s middle name?",
#     "What was the name of your first teacher?",
#     "What was the name of your best friend in childhood?",
#     "In what city were you born?",
#     "What year did you graduate high school?",
#     "What was the destination of your first flight?",
#     "What is the month and year of your oldest sibling’s birthday?",
#     "What is your favorite movie?",
#     "What is your favorite book as a child?",
#     "What is your favorite food?",
#     "What was your favorite subject in school?",
#     "What is your dream job?",
#     "What was the first website you remember visiting?",
#     "What is the name of your favorite childhood toy?",
#     "Who was your favorite cartoon character growing up?",
#     "What was the name of the first concert you attended?",
#     "What was your first job?"
# ]

# # Prepare documents
# documents = [{"question": q} for q in questions]

# # Insert into the collection
# result = collection.insert_many(documents)
# print(f"Inserted {len(result.inserted_ids)} security questions.")


# ============================================================================

users_collection = chat_db['users']

# Update all users that don't have security_question and security_answer fields
result = users_collection.update_many(
    {
        "$or": [
            {"security_question": {"$exists": False}},
            {"security_answer": {"$exists": False}}
        ]
    },
    {
        "$set": {
            "security_question": "",
            "security_answer": ""
        }
    }
)

print(f"Updated {result.modified_count} user(s) with empty security fields.")




# ==============================================================================





# Connect to SQLite
# sqlite_conn = sqlite3.connect("chatdatabase.db")
# sqlite_cursor = sqlite_conn.cursor()





#     # Get the database
# chat_db = client.get_database("chatDatabase")
# messages_collection = chat_db["messages"]

# # Add is_read field to all messages that don't have it
# result = messages_collection.update_many(
#     {"is_read": {"$exists": False}},  # Target only documents that lack this field
#     {"$set": {"is_read": False}}
# )

# print(f"Updated {result.modified_count} messages with is_read=False.")










# # Connect to MongoDB with GridFS
# mongo_client = MongoClient("mongodb+srv://udofiaubong10:qAWzNlJT6x2vSCdb@dsamessenger.tqp9u.mongodb.net", tlsCAFile=certifi.where())
# mongo_db = mongo_client["chatDatabase"]
# fs = gridfs.GridFS(mongo_db)

# # Create indexes for faster message retrieval
# mongo_db.messages.create_index([("group_id", 1)])
# mongo_db.messages.create_index([("private_chat_id", 1)])
# mongo_db.messages.create_index([("timestamp", -1)])

# print("✅ Indexes created successfully!")













# groups_collection = mongo_db["groups"]
# fs = gridfs.GridFS(mongo_db)


# # Define a default image ID or URL
# default_image_url = "/static/images/dsa-logo.png"  # Default image URL

# # Update all groups to include an image field
# result = groups_collection.update_many(
#     {},  # Empty filter means update all documents
#     {"$set": {"image": default_image_url}}  # Set default image field
# )

# print(f"Updated {result.modified_count} groups with an image field.")














# # Define the Civillian Staff Group ID
# civillian_staff_group_id = ObjectId("67c9082332874336da385fda")

# # Update all users by adding the 'groups' field and including the Civillian Staff group
# mongo_db.users.update_many(
#     {"groups": {"$exists": False}},  # Only users without the field will be updated
#     {"$set": {"groups": [civillian_staff_group_id]}}  # Add the general group
# )


# # Step 2: Migrate Users
# sqlite_cursor.execute("SELECT id, staffid, firstname, lastname, directorate, password, timestamp FROM users")
# users_mapping = {}  # SQLite user_id → MongoDB _id

# for user in sqlite_cursor.fetchall():
#     user_id, staffid, firstname, lastname, directorate, password, timestamp = user

#     # Image Handling - Store latest profile image in GridFS
#     image_id = None
#     image_path = os.path.normpath(f"uploads/{staffid}.jpg")  # Normalize path

#     if os.path.isfile(image_path):
#         with open(image_path, "rb") as image_file:
#             image_id = fs.put(image_file, filename=f"{staffid}.jpg")  # Overwrites old image
#     else:
#         print(f"⚠️ No profile image found for {staffid}, skipping...")

#     mongo_user_id = mongo_db.users.insert_one({
#         "staffid": staffid,
#         "firstname": firstname,
#         "lastname": lastname,
#         "directorate": directorate,
#         "password": password,
#         "timestamp": timestamp,
#         "image_id": str(image_id) if image_id else None  # Store GridFS image ID
#     }).inserted_id

#     users_mapping[user_id] = mongo_user_id  # Store user mapping

# print("✅ Users migrated successfully!")



# # Step 1: Migrate Groups and Store Mapping (SQLite id → MongoDB _id)
# sqlite_cursor.execute("SELECT id, name, timestamp FROM groups")
# group_mapping = {}

# for group in sqlite_cursor.fetchall():
#     sqlite_group_id, group_name, timestamp = group
#     mongo_group_id = mongo_db.groups.insert_one({
#         "name": group_name,
#         "timestamp": timestamp
#     }).inserted_id
#     group_mapping[sqlite_group_id] = mongo_group_id  # Store mapping

# print("✅ Groups migrated successfully!")



# # Step 3: Migrate User-Group Relationships
# sqlite_cursor.execute("SELECT user_id, group_id FROM user_groups")

# for user_id, group_id in sqlite_cursor.fetchall():
#     if user_id in users_mapping and group_id in group_mapping:
#         mongo_db.users.update_one(
#             {"_id": users_mapping[user_id]},
#             {"$addToSet": {"groups": group_mapping[group_id]}}
#         )

# print("✅ User-group relationships migrated!")



# # Step 4: Migrate Private Chats
# sqlite_cursor.execute("SELECT id, user1_id, user2_id FROM private_chats")
# private_chats = sqlite_cursor.fetchall()

# for chat in private_chats:
#     chat_id, user1_id, user2_id = chat

#     if user1_id in users_mapping and user2_id in users_mapping:
#         mongo_db.private_chats.insert_one({
#             "_id": ObjectId(),  # Generate a new ObjectId instead of using chat_id
#             "user1_id": users_mapping[user1_id],  # Map SQLite ID to MongoDB ObjectId
#             "user2_id": users_mapping[user2_id]   # Map SQLite ID to MongoDB ObjectId
#         })

# print("✅ Private chats migrated successfully!")



# # Step 4: Migrate Messages
# sqlite_cursor.execute("SELECT id, user_id, group_id, private_chat_id, message, message_type, timestamp FROM messages")

# for message in sqlite_cursor.fetchall():
#     msg_id, user_id, group_id, private_chat_id, message_text, message_type, timestamp = message

#     # Determine correct group or private chat reference
#     mongo_group_id = group_mapping.get(group_id, None)
#     mongo_private_chat_id = None if private_chat_id is None else ObjectId()

#     # Handle media files (images, videos, audio, etc.)
#     file_id = None
#     if message_type in ("image", "file", "audio", "video"):
#         file_path = os.path.normpath(f"uploads/{message_text}")  # Normalize path

#         if os.path.isfile(file_path):
#             with open(file_path, "rb") as file:
#                 file_id = fs.put(file, filename=message_text)  # Store in GridFS
#         else:
#             print(f"⚠️ File {file_path} not found, skipping...")

#     # Insert message into MongoDB
#     mongo_db.messages.insert_one({
#         "user_id": users_mapping[user_id],
#         "group_id": mongo_group_id,
#         "private_chat_id": mongo_private_chat_id,
#         "message": message_text if message_type == "text" else None,
#         "file_id": str(file_id) if file_id else None,
#         "message_type": message_type,
#         "timestamp": timestamp
#     })

# print("✅ Messages migrated successfully!")



# # Close connections
# sqlite_conn.close()
# mongo_client.close()