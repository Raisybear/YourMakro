import hashlib
import re
import uuid
from datetime import datetime
from app.models.user import User  # Import user model


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def is_valid_email(email):
    """Check if an email address is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_user(username, password, email=None):
    """Create a new user in the database."""
    from app.views.database import users_collection  # Import here to avoid circular imports

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
    """Verify login credentials."""
    from app.views.database import users_collection  # Import here to avoid circular imports

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