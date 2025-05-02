from datetime import datetime
from pymongo import MongoClient
import os


class Position:
    """Position model for mouse click positions and sets."""

    def __init__(self, username, set_name, positions=None, created_at=None, updated_at=None):
        """
        Initialize a Position instance.

        Args:
            username (str): The owner of this position set
            set_name (str): The name of this position set
            positions (list, optional): List of position dictionaries
            created_at (datetime, optional): When the set was created
            updated_at (datetime, optional): When the set was last updated
        """
        self.username = username
        self.set_name = set_name
        self.positions = positions or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    @staticmethod
    def get_collection():
        """Get the MongoDB collection for positions."""
        # Connect to the database using environment variables
        from dotenv import load_dotenv
        load_dotenv()
        MONGO_URI = os.getenv("MONGO_URI")
        client = MongoClient(MONGO_URI)
        db = client["mouse_clicker"]
        return db["mousePositions"]

    def to_dict(self):
        """Convert Position instance to dictionary for database storage."""
        return {
            "username": self.username,
            "set_name": self.set_name,
            "positions": self.positions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, position_dict):
        """Create a Position instance from a database dictionary."""
        return cls(
            username=position_dict["username"],
            set_name=position_dict["set_name"],
            positions=position_dict["positions"],
            created_at=position_dict["created_at"],
            updated_at=position_dict.get("updated_at", position_dict["created_at"])
        )

    def save(self, update_existing=False):
        """Save or update positions in MongoDB."""
        if not self.positions:
            return False

        positions_collection = self.get_collection()

        if update_existing:
            # Update existing set
            result = positions_collection.update_one(
                {"username": self.username, "set_name": self.set_name},
                {"$set": {
                    "positions": self.positions,
                    "updated_at": datetime.now()
                }}
            )
            return result.modified_count > 0
        else:
            # Check if set exists
            existing = positions_collection.find_one({"username": self.username, "set_name": self.set_name})
            if existing:
                # Update if exists
                return self.save(update_existing=True)
            else:
                # Create new set
                positions_collection.insert_one(self.to_dict())
                return True

    @classmethod
    def load(cls, username, set_name):
        """Load positions for a specific set."""
        positions_collection = cls.get_collection()
        set_data = positions_collection.find_one({"username": username, "set_name": set_name})
        if set_data:
            return cls.from_dict(set_data)
        return None

    @classmethod
    def get_user_sets(cls, username):
        """Get all sets for a user."""
        positions_collection = cls.get_collection()
        sets = positions_collection.find({"username": username})
        return [cls.from_dict(s) for s in sets]

    @staticmethod
    def get_all_sets_info(username):
        """Get simplified information about all sets for a user."""
        positions_collection = Position.get_collection()
        sets = positions_collection.find({"username": username})
        return [{"name": s["set_name"],
                 "positions": len(s["positions"]),
                 "created_at": s["created_at"],
                 "updated_at": s.get("updated_at", s["created_at"])}
                for s in sets]

    @classmethod
    def delete(cls, username, set_name):
        """Delete a position set."""
        positions_collection = cls.get_collection()
        result = positions_collection.delete_one({"username": username, "set_name": set_name})
        return result.deleted_count > 0

    @classmethod
    def create_empty_set(cls, username, set_name):
        """Create a new empty position set."""
        positions_collection = cls.get_collection()
        # Check if set exists first
        existing = positions_collection.find_one({"username": username, "set_name": set_name})
        if existing:
            return False

        # Create new empty set
        position_set = cls(username=username, set_name=set_name)
        positions_collection.insert_one(position_set.to_dict())
        return True

    @staticmethod
    def get_all_users():
        """Get list of all users who have position sets."""
        positions_collection = Position.get_collection()
        return positions_collection.distinct("username")