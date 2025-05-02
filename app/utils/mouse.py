import pyautogui
import time
import keyboard
from pynput.mouse import Listener
from datetime import datetime
from app.views.database import positions_collection

# Global variables
positions = []
adding_positions = False


def on_click(x, y, button, pressed):
    """Handle mouse clicks for position recording."""
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
            exit()
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


def start_clicking(click_speed=0.5):
    """Execute clicking action."""
    global positions

    if not positions:
        print("No positions saved. Exiting.")
        return

    print(f"Starting in 3 seconds. Press ESC to stop. Click speed: {click_speed}s")
    time.sleep(3)

    while True:
        if keyboard.is_pressed("esc"):
            print("Script stopped.")
            exit()

        for pos in positions:
            if keyboard.is_pressed("esc"):
                print("Script stopped.")
                exit()

            pyautogui.moveTo(pos["x"], pos["y"])
            pyautogui.click()
            print(f"Clicked at: {pos}")

            time.sleep(click_speed)


def save_positions(username, set_name, update_existing=False):
    """Save or update positions in MongoDB."""
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
    """Load positions for a specific set."""
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
    """Get all sets for a user."""
    sets = positions_collection.find({"username": username})
    return [{"name": s["set_name"], "positions": len(s["positions"]),
             "created_at": s["created_at"],
             "updated_at": s.get("updated_at", s["created_at"])} for s in sets]


def delete_set(username, set_name):
    """Delete a position set."""
    result = positions_collection.delete_one({"username": username, "set_name": set_name})
    return result.deleted_count > 0