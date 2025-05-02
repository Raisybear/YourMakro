import hashlib
from datetime import datetime
import uuid
import re
from pymongo import MongoClient
import os


class User:
    """User model for authentication and database operations."""

    def __init__(self, username, password=None, email=None, user_id=None,
                 created_at=None, last_login=None):
        """
        Initialize a User instance.

        Args:
            username (str): The username
            password (str, optional): The user's password (unhashed)
            email (str, optional): The user's email
            user_id (str, optional): User ID (UUID)
            created_at (datetime, optional): When the user was created
            last_login (datetime, optional): Last login timestamp
        """
        self.username = username
        self._password = password  # Underscore to indicate it's not stored directly
        self.email = email
        self.user_id = user_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.now()
        self.last_login = last_login

    @staticmethod
    def get_collection():
        """Get the MongoDB collection for users."""
        # Connect to the database using environment variables
        from dotenv import load_dotenv
        load_dotenv()
        MONGO_URI = os.getenv("MONGO_URI")
        client = MongoClient(MONGO_URI)
        db = client["mouse_clicker"]
        return db["users"]

    @staticmethod
    def hash_password(password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def is_valid_email(email):
        """Check if an email address is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def to_dict(self):
        """Convert User instance to dictionary for database storage."""
        user_dict = {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at,
            "last_login": self.last_login
        }

        # Only include password if it exists (for new users)
        if self._password:
            user_dict["password"] = self.hash_password(self._password)

        # Only include email if it exists
        if self.email:
            user_dict["email"] = self.email

        return user_dict

    @classmethod
    def from_dict(cls, user_dict):
        """Create a User instance from a database dictionary."""
        return cls(
            username=user_dict["username"],
            email=user_dict.get("email"),
            user_id=user_dict["user_id"],
            created_at=user_dict["created_at"],
            last_login=user_dict.get("last_login")
        )

    def save(self):
        """Save user to database."""
        users_collection = self.get_collection()
        user_data = self.to_dict()

        # Check if user exists
        existing_user = users_collection.find_one({"user_id": self.user_id})

        if existing_user:
            # Update existing user
            users_collection.update_one(
                {"user_id": self.user_id},
                {"$set": user_data}
            )
            return True
        else:
            # Create new user
            users_collection.insert_one(user_data)
            return True

    @classmethod
    def create_user(cls, username, password, email=None):
        """Create a new user in the database."""
        # Validation
        if not username or not password:
            return False, "Username and password are required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        if email and not cls.is_valid_email(email):
            return False, "Invalid email format"

        # Check if user exists - modified query to handle empty email
        users_collection = cls.get_collection()
        query = {"username": username}
        if email:
            query = {"$or": [{"username": username}, {"email": email}]}

        if users_collection.find_one(query):
            return False, "Username or email already exists"

        # Create user
        user = cls(username=username, password=password, email=email)
        user.save()
        return True, "User created successfully"

    @classmethod
    def verify_credentials(cls, username_or_email, password):
        """Verify login credentials."""
        users_collection = cls.get_collection()
        user = users_collection.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })

        if user and cls.hash_password(password) == user["password"]:
            # Update last login
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            return True, user["username"]
        return False, None

    @classmethod
    def get_by_username(cls, username):
        """Get a user by username."""
        users_collection = cls.get_collection()
        user_data = users_collection.find_one({"username": username})
        if user_data:
            return cls.from_dict(user_data)
        return None