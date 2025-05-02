from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
users_collection = db["users"]
positions_collection = db["mousePositions"]


def get_user_by_username(username):
    """Get user data by username.

    Args:
        username (str): The username

    Returns:
        dict: User data or None
    """
    return users_collection.find_one({"username": username})


def get_user_by_email(email):
    """Get user data by email.

    Args:
        email (str): The email address

    Returns:
        dict: User data or None
    """
    return users_collection.find_one({"email": email})


def get_user_by_id(user_id):
    """Get user data by user_id.

    Args:
        user_id (str): The user ID

    Returns:
        dict: User data or None
    """
    return users_collection.find_one({"user_id": user_id})


def update_last_login(username):
    """Update the user's last login timestamp.

    Args:
        username (str): The username

    Returns:
        bool: True if updated successfully
    """
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.now()}}
    )
    return result.modified_count > 0


def update_user_profile(username, update_data):
    """Update user profile information.

    Args:
        username (str): The username
        update_data (dict): Data to update

    Returns:
        bool: True if updated successfully
    """
    # Don't allow updating the username or user_id
    if "username" in update_data:
        del update_data["username"]
    if "user_id" in update_data:
        del update_data["user_id"]

    update_data["updated_at"] = datetime.now()

    result = users_collection.update_one(
        {"username": username},
        {"$set": update_data}
    )
    return result.modified_count > 0


def get_user_statistics(username):
    """Get user statistics.

    Args:
        username (str): The username

    Returns:
        dict: User statistics
    """
    # Get user data
    user = get_user_by_username(username)
    if not user:
        return None

    # Get user's sets
    sets = positions_collection.find({"username": username})

    # Compile statistics
    stats = {
        "total_sets": positions_collection.count_documents({"username": username}),
        "total_positions": 0,
        "newest_set": None,
        "last_login": user.get("last_login"),
        "account_age": datetime.now() - user.get("created_at"),
    }

    newest_time = None
    for s in sets:
        positions_count = len(s.get("positions", []))
        stats["total_positions"] += positions_count

        updated_at = s.get("updated_at", s.get("created_at"))
        if newest_time is None or updated_at > newest_time:
            newest_time = updated_at
            stats["newest_set"] = {
                "name": s["set_name"],
                "positions": positions_count,
                "updated_at": updated_at
            }

    return stats


def delete_user_account(username):
    """Delete a user account and all associated data.

    Args:
        username (str): The username

    Returns:
        bool: True if deleted successfully
    """
    # Delete all position sets
    positions_collection.delete_many({"username": username})

    # Delete user account
    result = users_collection.delete_one({"username": username})
    return result.deleted_count > 0