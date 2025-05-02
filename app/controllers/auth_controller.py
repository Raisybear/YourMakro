import hashlib
import re
import uuid
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
users_collection = db["users"]


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def is_valid_email(email):
    """Check if an email address is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_user(username, password, email=None):
    """Create a new user in the database.

    Args:
        username (str): The username
        password (str): The password
        email (str, optional): The email address

    Returns:
        tuple: (success, message)
    """
    # Validation
    if not username or not password:
        return False, "Username and password are required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    if email and not is_valid_email(email):
        return False, "Invalid email format"

    # Check if user exists - modified query to handle empty email
    query = {"username": username}
    if email:
        query = {"$or": [{"username": username}, {"email": email}]}

    if users_collection.find_one(query):
        return False, "Username or email already exists"

    # Create user
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password": hash_password(password),
        "created_at": datetime.now(),
        "last_login": None
    }

    if email:
        user_data["email"] = email

    users_collection.insert_one(user_data)
    return True, "User created successfully"


def verify_credentials(username_or_email, password):
    """Verify login credentials.

    Args:
        username_or_email (str): The username or email
        password (str): The password

    Returns:
        tuple: (success, username)
    """
    user = users_collection.find_one({
        "$or": [
            {"username": username_or_email},
            {"email": username_or_email}
        ]
    })

    if user and hash_password(password) == user["password"]:
        # Update last login
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now()}}
        )
        return True, user["username"]
    return False, None


def get_all_users():
    """Get a list of all users.

    Returns:
        list: List of usernames
    """
    users = users_collection.find({}, {"username": 1})
    return [user["username"] for user in users]