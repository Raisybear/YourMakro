import pyautogui
import time
import keyboard
from pymongo import MongoClient
from pynput.mouse import Listener
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import customtkinter as ctk
import hashlib
from datetime import datetime

# Verbindung zu MongoDB Atlas
MONGO_URI = "mongodb+srv://spycherelias7:ms23fzCUupdwjTeB@mousepositions.jugnj14.mongodb.net/?retryWrites=true&w=majority&appName=mousePositions"
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
positions_collection = db["mousePositions"]
users_collection = db["users"]

positions = []
current_set_name = ""


def hash_password(password):
    """Hasht ein Passwort mit SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_user(username, password):
    """Erstellt einen neuen Benutzer in der Datenbank."""
    hashed_password = hash_password(password)
    if users_collection.find_one({"username": username}):
        return False, "Benutzername bereits vorhanden."
    users_collection.insert_one({"username": username, "password": hashed_password})
    return True, "Benutzer erfolgreich erstellt."


def verify_password(username, password):
    """Überprüft das Passwort eines Benutzers."""
    user = users_collection.find_one({"username": username})
    if user:
        hashed_password = user["password"]
        if hash_password(password) == hashed_password:
            return True
    return False


def save_positions(username, set_name):
    """Speichert Positionen in MongoDB unter dem Benutzernamen und Set-Namen."""
    if positions:
        positions_collection.insert_one({
            "username": username,
            "set_name": set_name,
            "positions": positions,
            "created_at": datetime.now()
        })
        print(f"Positionen für {username} (Set: {set_name}) wurden in der Datenbank gespeichert!")


def load_positions(username, set_name):
    """Lädt die Positionen eines bestimmten Sets eines Benutzers aus MongoDB."""
    global positions
    set_data = positions_collection.find_one({"username": username, "set_name": set_name})
    if set_data:
        positions = set_data["positions"]
        print(f"Gespeicherte Positionen für {username} (Set: {set_name}) geladen!")
        return True
    else:
        print(f"Keine gespeicherten Positionen für {username} (Set: {set_name}) gefunden.")
        return False


def get_user_sets(username):
    """Gibt alle Sets eines Benutzers zurück."""
    sets = positions_collection.find({"username": username})
    return [{"name": s["set_name"], "positions": len(s["positions"]), "created_at": s["created_at"]} for s in sets]


def delete_set(username, set_name):
    """Löscht ein Positionsset eines Benutzers."""
    result = positions_collection.delete_one({"username": username, "set_name": set_name})
    return result.deleted_count > 0


def on_click(x, y, button, pressed):
    """Speichert Position und Auflösung beim Linksklick und beendet beim Rechtsklick."""
    if pressed:
        if keyboard.is_pressed("esc"):
            print("Skript gestoppt.")
            exit()
        if str(button) == "Button.left":
            resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
            positions.append({"x": x, "y": y, "resolution": resolution})
            print(f"Position gespeichert: {x}, {y}, Auflösung: {resolution}")
        elif str(button) == "Button.right":
            print("Erfassung abgeschlossen!")
            return False


def get_positions():
    """Startet den Listener zur Positionserfassung."""
    print("Klicke auf die gewünschten Positionen. Rechtsklick zum Beenden.")
    with Listener(on_click=on_click) as listener:
        listener.join()


def start_clicking():
    """Führt die Klick-Aktion aus."""
    if not positions:
        print("Keine Positionen gespeichert. Beende das Programm.")
        return

    print("Das Skript startet in 3 Sekunden. Drücke ESC zum Abbrechen.")
    time.sleep(3)

    while True:
        if keyboard.is_pressed("esc"):
            print("Skript gestoppt.")
            exit()

        for pos in positions:
            if keyboard.is_pressed("esc"):
                print("Skript gestoppt.")
                exit()

            pyautogui.moveTo(pos["x"], pos["y"])
            pyautogui.click()
            print(f"Geklickt auf: {pos}")

            time.sleep(0.5)


class MouseClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mouse Clicker Pro")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Variables
        self.username = tk.StringVar()
        self.set_name = tk.StringVar()
        self.clickThread = None
        self.recording = False
        self.login_successful = False
        self.currently_logged_in = None

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Create login UI initially
        self.create_login_ui()

        # Bind ESC key
        self.bind("<Escape>", self.stop_operations)

    def create_login_ui(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)

        # Username
        ctk.CTkLabel(self.login_frame, text="Username:").pack(pady=(10, 0))
        self.username_entry = ctk.CTkEntry(self.login_frame)
        self.username_entry.pack(pady=(0, 10))

        # Password
        ctk.CTkLabel(self.login_frame, text="Password:").pack(pady=(10, 0))
        self.password_entry = ctk.CTkEntry(self.login_frame, show="*")
        self.password_entry.pack(pady=(0, 10))

        # Buttons
        ctk.CTkButton(self.login_frame, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(self.login_frame, text="Register", command=self.register).pack(pady=10)

    def create_main_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Main content
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Configure sidebar
        self.create_sidebar()

        # Configure main content
        self.create_main_content()

    def create_sidebar(self):
        # User info
        user_frame = ctk.CTkFrame(self.sidebar)
        user_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(user_frame, text=f"Logged in as:",
                     font=ctk.CTkFont(size=12)).pack()
        ctk.CTkLabel(user_frame, text=f"{self.currently_logged_in}",
                     font=ctk.CTkFont(size=14, weight="bold")).pack()

        # Logout button
        ctk.CTkButton(user_frame, text="Logout", command=self.logout,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90")).pack(pady=10, fill="x")

        # Set management
        set_frame = ctk.CTkFrame(self.sidebar)
        set_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(set_frame, text="Set Name:").pack(pady=(5, 0))
        self.set_name_entry = ctk.CTkEntry(set_frame)
        self.set_name_entry.pack(pady=(0, 5), fill="x")

        ctk.CTkButton(set_frame, text="Create New Set", command=self.create_new_set).pack(pady=5, fill="x")
        ctk.CTkButton(set_frame, text="Delete Selected Set", command=self.delete_selected_set,
                      fg_color="#D35B58", hover_color="#C77C78").pack(pady=5, fill="x")

        # Browse other users
        browse_frame = ctk.CTkFrame(self.sidebar)
        browse_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(browse_frame, text="Browse Other Users",
                      command=self.show_user_browser).pack(pady=5, fill="x")

        # Actions
        action_frame = ctk.CTkFrame(self.sidebar)
        action_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(action_frame, text="Record Positions", command=self.start_recording).pack(pady=5, fill="x")
        ctk.CTkButton(action_frame, text="Start Clicking", command=self.start_clicking).pack(pady=5, fill="x")
        ctk.CTkButton(action_frame, text="Stop", command=self.stop_operations,
                      fg_color="#D35B58", hover_color="#C77C78").pack(pady=5, fill="x")

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar, text="Ready")
        self.status_label.pack(side="bottom", pady=10)

    def create_main_content(self):
        # Sets list
        sets_frame = ctk.CTkFrame(self.main_content)
        sets_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview for sets
        self.sets_tree = ttk.Treeview(sets_frame, columns=("name", "positions", "created"), show="headings")
        self.sets_tree.heading("name", text="Set Name")
        self.sets_tree.heading("positions", text="Positions")
        self.sets_tree.heading("created", text="Created At")

        self.sets_tree.column("name", width=200)
        self.sets_tree.column("positions", width=100)
        self.sets_tree.column("created", width=200)

        scrollbar = ttk.Scrollbar(sets_frame, orient="vertical", command=self.sets_tree.yview)
        self.sets_tree.configure(yscrollcommand=scrollbar.set)

        self.sets_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load user's sets
        self.load_user_sets()

        # Positions table
        positions_frame = ctk.CTkFrame(self.main_content)
        positions_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.positions_tree = ttk.Treeview(positions_frame, columns=("index", "x", "y", "resolution"), show="headings")
        self.positions_tree.heading("index", text="#")
        self.positions_tree.heading("x", text="X")
        self.positions_tree.heading("y", text="Y")
        self.positions_tree.heading("resolution", text="Resolution")

        self.positions_tree.column("index", width=50)
        self.positions_tree.column("x", width=100)
        self.positions_tree.column("y", width=100)
        self.positions_tree.column("resolution", width=150)

        scrollbar = ttk.Scrollbar(positions_frame, orient="vertical", command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)

        self.positions_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind set selection
        self.sets_tree.bind("<<TreeviewSelect>>", self.on_set_select)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        success, message = create_user(username, password)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        if verify_password(username, password):
            self.currently_logged_in = username
            self.username.set(username)
            self.login_frame.destroy()
            self.create_main_ui()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def load_user_sets(self):
        # Clear existing items
        for item in self.sets_tree.get_children():
            self.sets_tree.delete(item)

        # Load sets from database
        sets = get_user_sets(self.currently_logged_in)
        for s in sets:
            self.sets_tree.insert("", "end", values=(
                s["name"],
                s["positions"],
                s["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            ))

    def on_set_select(self, event):
        selected = self.sets_tree.selection()
        if selected:
            set_name = self.sets_tree.item(selected[0])["values"][0]
            self.set_name.set(set_name)
            self.set_name_entry.delete(0, tk.END)
            self.set_name_entry.insert(0, set_name)

            # Load positions for this set
            if load_positions(self.currently_logged_in, set_name):
                self.update_positions_display()

    def create_new_set(self):
        set_name = self.set_name_entry.get()
        if not set_name:
            messagebox.showerror("Error", "Please enter a set name")
            return

        # Check if set already exists
        existing = positions_collection.find_one({"username": self.currently_logged_in, "set_name": set_name})
        if existing:
            messagebox.showerror("Error", "A set with this name already exists")
            return

        # Create empty set
        positions_collection.insert_one({
            "username": self.currently_logged_in,
            "set_name": set_name,
            "positions": [],
            "created_at": datetime.now()
        })

        self.load_user_sets()
        messagebox.showinfo("Success", f"Set '{set_name}' created")

    def delete_selected_set(self):
        selected = self.sets_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a set to delete")
            return

        set_name = self.sets_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete set '{set_name}'?"):
            if delete_set(self.currently_logged_in, set_name):
                self.load_user_sets()
                self.positions_tree.delete(*self.positions_tree.get_children())
                messagebox.showinfo("Success", f"Set '{set_name}' deleted")
            else:
                messagebox.showerror("Error", "Failed to delete set")

    def show_user_browser(self):
        """Zeigt einen Dialog zum Durchsuchen anderer Benutzer und ihrer Sets an."""
        all_users = positions_collection.distinct("username")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Browse Other Users")
        dialog.geometry("800x600")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        user_frame = ctk.CTkFrame(main_frame, width=200)
        user_frame.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(user_frame, text="Users", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        self.user_listbox = tk.Listbox(user_frame, font=("Arial", 12))
        self.user_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        for user in all_users:
            if user != self.currently_logged_in:
                self.user_listbox.insert(tk.END, user)

        sets_frame = ctk.CTkFrame(main_frame)
        sets_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(sets_frame, text="Sets", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        self.browser_sets_tree = ttk.Treeview(sets_frame, columns=("name", "positions", "created"), show="headings")
        self.browser_sets_tree.heading("name", text="Set Name")
        self.browser_sets_tree.heading("positions", text="Positions")
        self.browser_sets_tree.heading("created", text="Created At")

        self.browser_sets_tree.column("name", width=200)
        self.browser_sets_tree.column("positions", width=100)
        self.browser_sets_tree.column("created", width=200)

        scrollbar = ttk.Scrollbar(sets_frame, orient="vertical", command=self.browser_sets_tree.yview)
        self.browser_sets_tree.configure(yscrollcommand=scrollbar.set)

        self.browser_sets_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        copy_frame = ctk.CTkFrame(sets_frame)
        copy_frame.pack(fill="x", pady=10)

        ctk.CTkButton(copy_frame, text="Copy Selected Set",
                      command=lambda: self.copy_selected_set(dialog)).pack(pady=5)

        self.user_listbox.bind("<<ListboxSelect>>", lambda e: self.load_user_sets_for_browser())

    def load_user_sets_for_browser(self):
        """Lädt die Sets des ausgewählten Benutzers in den Browser."""
        selected = self.user_listbox.curselection()
        if not selected:
            return

        username = self.user_listbox.get(selected[0])
        sets = get_user_sets(username)

        for item in self.browser_sets_tree.get_children():
            self.browser_sets_tree.delete(item)

        for s in sets:
            self.browser_sets_tree.insert("", "end", values=(
                s["name"],
                s["positions"],
                s["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            ))

    def copy_selected_set(self, dialog):
        """Kopiert das ausgewählte Set zum aktuellen Benutzer."""
        user_selected = self.user_listbox.curselection()
        set_selected = self.browser_sets_tree.selection()

        if not user_selected or not set_selected:
            messagebox.showerror("Error", "Please select both a user and a set")
            return

        source_user = self.user_listbox.get(user_selected[0])
        set_name = self.browser_sets_tree.item(set_selected[0])["values"][0]

        set_data = positions_collection.find_one({"username": source_user, "set_name": set_name})
        if not set_data:
            messagebox.showerror("Error", "Selected set not found")
            return

        new_name = f"{set_name} (from {source_user})"
        counter = 1
        while positions_collection.find_one({"username": self.currently_logged_in, "set_name": new_name}):
            new_name = f"{set_name} (from {source_user}) {counter}"
            counter += 1

        positions_collection.insert_one({
            "username": self.currently_logged_in,
            "set_name": new_name,
            "positions": set_data["positions"],
            "created_at": datetime.now()
        })

        messagebox.showinfo("Success", f"Set '{set_name}' copied as '{new_name}'")
        dialog.destroy()
        self.load_user_sets()

    def start_recording(self):
        global positions

        set_name = self.set_name_entry.get()
        if not set_name:
            messagebox.showerror("Error", "Please select or create a set first")
            return

        positions = []
        self.update_status("Recording positions. Left click to record, right click to finish.")

        threading.Thread(target=self.recording_thread, args=(set_name,), daemon=True).start()

    def recording_thread(self, set_name):
        get_positions()
        self.after(0, self.recording_finished, set_name)

    def recording_finished(self, set_name):
        save_positions(self.currently_logged_in, set_name)
        self.load_user_sets()
        self.update_positions_display()
        self.update_status(f"Recorded {len(positions)} positions in set '{set_name}'")

    def start_clicking(self):
        if not positions:
            messagebox.showerror("Error", "No positions to click")
            return

        self.update_status("Starting in 3 seconds... Press ESC to stop")
        threading.Thread(target=self.clicking_thread, daemon=True).start()

    def clicking_thread(self):
        time.sleep(3)
        start_clicking()
        self.after(0, self.update_status, "Clicking finished")

    def stop_operations(self, event=None):
        self.clickThread = None
        self.update_status("Stopped")

    def logout(self):
        """Logs out the current user and returns to login screen."""
        try:
            # Stop any ongoing operations first
            self.stop_operations()

            # Clear current user data
            self.currently_logged_in = None
            self.username.set("")

            # Clear positions
            global positions
            positions = []

            # Check if widgets exist before destroying
            if hasattr(self, 'sidebar') and self.sidebar.winfo_exists():
                self.sidebar.destroy()

            if hasattr(self, 'main_content') and self.main_content.winfo_exists():
                self.main_content.destroy()

            # Recreate login UI
            self.create_login_ui()

            # Show logout confirmation
            messagebox.showinfo("Info", "Logged out successfully")
        except Exception as e:
            print(f"Error during logout: {e}")
            # Fallback - recreate the entire window if something went wrong
            self.destroy()
            self.__init__()
            self.create_login_ui()

    def update_status(self, message):
        self.status_label.configure(text=message)

    def update_positions_display(self):
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)

        for i, pos in enumerate(positions, 1):
            self.positions_tree.insert("", "end", values=(
                i,
                pos["x"],
                pos["y"],
                pos["resolution"]
            ))


if __name__ == "__main__":
    app = MouseClickerApp()
    app.mainloop()