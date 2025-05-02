import pyautogui
import keyboard
import time
from datetime import datetime
from pymongo import MongoClient
from pynput.mouse import Listener
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
positions_collection = db["mousePositions"]

# Global variables
positions = []
adding_positions = False
click_speed = 0.5  # Default click speed in seconds


def save_positions(username, set_name, update_existing=False):
    """Save or update positions in MongoDB.

    Args:
        username (str): The username of the user
        set_name (str): The name of the position set
        update_existing (bool): Whether to update an existing set

    Returns:
        bool: True if saved successfully, False otherwise
    """
    if not positions:
        return False

    if update_existing:
        # Update existing set
        result = positions_collection.update_one(
            {"username": username, "set_name": set_name},
            {"$set": {
                "positions": positions,
                "updated_at": datetime.now()
            }}
        )
        if result.modified_count > 0:
            print(f"Positions for {username} (Set: {set_name}) updated!")
            return True
    else:
        # Create new set
        positions_collection.insert_one({
            "username": username,
            "set_name": set_name,
            "positions": positions,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"Positions for {username} (Set: {set_name}) saved to database!")
        return True

    return False


def load_positions(username, set_name):
    """Load positions for a specific set.

    Args:
        username (str): The username of the user
        set_name (str): The name of the position set

    Returns:
        bool: True if loaded successfully, False otherwise
    """
    global positions
    set_data = positions_collection.find_one({"username": username, "set_name": set_name})
    if set_data:
        positions = set_data["positions"]
        print(f"Saved positions for {username} (Set: {set_name}) loaded!")
        return True
    else:
        print(f"No saved positions found for {username} (Set: {set_name})")
        return False


def get_user_sets(username):
    """Get all sets for a user.

    Args:
        username (str): The username of the user

    Returns:
        list: List of set information dictionaries
    """
    sets = positions_collection.find({"username": username})
    return [{"name": s["set_name"], "positions": len(s["positions"]),
             "created_at": s["created_at"],
             "updated_at": s.get("updated_at", s["created_at"])} for s in sets]


def delete_set(username, set_name):
    """Delete a position set.

    Args:
        username (str): The username of the user
        set_name (str): The name of the position set

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    result = positions_collection.delete_one({"username": username, "set_name": set_name})
    return result.deleted_count > 0


def copy_set(source_user, set_name, target_user, new_name=None):
    """Copy a position set from one user to another.

    Args:
        source_user (str): The username of the source user
        set_name (str): The name of the position set to copy
        target_user (str): The username of the target user
        new_name (str, optional): The new name for the copied set

    Returns:
        tuple: (success, message or new_name)
    """
    set_data = positions_collection.find_one({"username": source_user, "set_name": set_name})
    if not set_data:
        return False, "Selected set not found"

    if new_name is None:
        new_name = f"{set_name} (from {source_user})"
        counter = 1
        while positions_collection.find_one({"username": target_user, "set_name": new_name}):
            new_name = f"{set_name} (from {source_user}) {counter}"
            counter += 1

    positions_collection.insert_one({
        "username": target_user,
        "set_name": new_name,
        "positions": set_data["positions"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })

    return True, new_name


def create_empty_set(username, set_name):
    """Create a new empty position set.

    Args:
        username (str): The username of the user
        set_name (str): The name of the position set

    Returns:
        bool: True if created successfully, False otherwise
    """
    if positions_collection.find_one({"username": username, "set_name": set_name}):
        return False

    positions_collection.insert_one({
        "username": username,
        "set_name": set_name,
        "positions": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })
    return True


def on_click(x, y, button, pressed):
    """Handle mouse clicks for position recording.

    Args:
        x (int): X coordinate
        y (int): Y coordinate
        button: Mouse button
        pressed (bool): Whether button was pressed

    Returns:
        bool: False to stop listener, True to continue
    """
    global adding_positions, positions

    if pressed and adding_positions:
        if str(button) == "Button.left":
            resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
            positions.append({"x": x, "y": y, "resolution": resolution})
            print(f"Position saved: {x}, {y}, Resolution: {resolution}")
            return True
        elif str(button) == "Button.right":
            print("Position recording stopped")
            adding_positions = False
            return False

    elif pressed:
        if keyboard.is_pressed("esc"):
            print("Script stopped.")
            return False
        if str(button) == "Button.left":
            resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
            positions.append({"x": x, "y": y, "resolution": resolution})
            print(f"Position saved: {x}, {y}, Resolution: {resolution}")
        elif str(button) == "Button.right":
            print("Recording complete!")
            return False


def get_positions():
    """Start listener for position recording."""
    print("Click desired positions. Right-click to finish.")
    with Listener(on_click=on_click) as listener:
        listener.join()


def start_adding_positions():
    """Start multi-position adding mode."""
    global adding_positions
    adding_positions = True
    print("Click desired positions. Right-click to finish.")

    def add_positions_thread():
        with Listener(on_click=on_click) as listener:
            listener.join()

    threading.Thread(target=add_positions_thread, daemon=True).start()


def start_clicking():
    """Execute clicking action."""
    global click_speed

    if not positions:
        print("No positions saved. Exiting.")
        return

    print(f"Starting in 3 seconds. Press ESC to stop. Click speed: {click_speed}s")
    time.sleep(3)

    try:
        while True:
            if keyboard.is_pressed("esc"):
                print("Script stopped.")
                break

            for pos in positions:
                if keyboard.is_pressed("esc"):
                    print("Script stopped.")
                    return

                pyautogui.moveTo(pos["x"], pos["y"])
                pyautogui.click()
                print(f"Clicked at: {pos}")

                time.sleep(click_speed)
    except Exception as e:
        print(f"Error during clicking: {e}")


def set_click_speed(speed):
    """Set the click speed.

    Args:
        speed (float): The click speed in seconds
    """
    global click_speed
    click_speed = speed
    print(f"Click speed set to {click_speed} seconds")