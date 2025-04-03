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
from PIL import Image, ImageTk, ImageDraw
import math
from dotenv import load_dotenv
import os

# Verbindung zu MongoDB Atlas
load_dotenv()  # This loads the .env file
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
positions_collection = db["mousePositions"]
users_collection = db["users"]

positions = []
current_set_name = ""
adding_positions = False
click_speed = 0.5  # Default click speed in seconds


# Hilfsfunktionen
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


def save_positions(username, set_name, update_existing=False):
    """Speichert oder aktualisiert Positionen in MongoDB."""
    if not positions:
        return False

    if update_existing:
        # Aktualisiere vorhandenes Set
        result = positions_collection.update_one(
            {"username": username, "set_name": set_name},
            {"$set": {
                "positions": positions,
                "updated_at": datetime.now()
            }}
        )
        if result.modified_count > 0:
            print(f"Positionen für {username} (Set: {set_name}) wurden aktualisiert!")
            return True
    else:
        # Erstelle neues Set
        positions_collection.insert_one({
            "username": username,
            "set_name": set_name,
            "positions": positions,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"Positionen für {username} (Set: {set_name}) wurden in der Datenbank gespeichert!")
        return True

    return False


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
    return [{"name": s["set_name"], "positions": len(s["positions"]),
             "created_at": s["created_at"],
             "updated_at": s.get("updated_at", s["created_at"])} for s in sets]


def delete_set(username, set_name):
    """Löscht ein Positionsset eines Benutzers."""
    result = positions_collection.delete_one({"username": username, "set_name": set_name})
    return result.deleted_count > 0


def on_click(x, y, button, pressed):
    """Speichert Position und Auflösung beim Linksklick und beendet beim Rechtsklick."""
    global adding_positions, positions

    if pressed and adding_positions:
        if str(button) == "Button.left":
            resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
            positions.append({"x": x, "y": y, "resolution": resolution})
            print(f"Position gespeichert: {x}, {y}, Auflösung: {resolution}")
            return True  # Listener bleibt aktiv für weitere Klicks
        elif str(button) == "Button.right":
            print("Positionserfassung beendet")
            adding_positions = False
            return False  # Beendet den Listener

    elif pressed:  # Normale Aufnahme (nicht im Mehrfach-Add-Modus)
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


def start_adding_positions():
    """Startet den Modus zum Hinzufügen mehrerer Positionen."""
    global adding_positions
    adding_positions = True
    messagebox.showinfo("Info", "Klicken Sie auf die gewünschten Positionen. Rechtsklick zum Beenden.")

    def add_positions_thread():
        with Listener(on_click=on_click) as listener:
            listener.join()

    threading.Thread(target=add_positions_thread, daemon=True).start()


def start_clicking():
    """Führt die Klick-Aktion aus."""
    global click_speed

    if not positions:
        print("Keine Positionen gespeichert. Beende das Programm.")
        return

    print(f"Das Skript startet in 3 Sekunden. Drücke ESC zum Abbrechen. Klickgeschwindigkeit: {click_speed}s")
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

            time.sleep(click_speed)


def create_drag_icon():
    """Erstellt ein ansprechendes Drag-Icon mit Pillow"""
    # Erstelle ein transparentes Bild
    img = Image.new('RGBA', (100, 40), (0, 0, 0, 0))

    # Zeichne einen modernen "Drag" Hinweis
    draw = ImageDraw.Draw(img)

    # Hintergrund mit abgerundeten Ecken
    draw.rounded_rectangle([(0, 0), (100, 40)], 15, fill=(70, 130, 180, 200))

    # Text und Pfeile
    draw.text((20, 10), "Drag", fill=(255, 255, 255, 255))
    draw.line([(70, 15), (85, 15), (80, 10)], fill=(255, 255, 255), width=2)
    draw.line([(70, 25), (85, 25), (80, 30)], fill=(255, 255, 255), width=2)

    return img  # Rückgabe des PIL Image Objekts statt PhotoImage


class DragManager:
    """Klasse zur Verwaltung der Drag & Drop Animationen"""

    def __init__(self, root):
        self.root = root
        self.drag_label = None
        self.drag_start_pos = (0, 0)
        self.current_item = None
        self.ghost_image = create_drag_icon()
        self.animation_id = None
        self.target_pos = (0, 0)
        self.drag_source = None  # Hinzugefügt

    def start_drag(self, event, tree, item):
        """Startet den Drag-Vorgang mit Animation"""
        self.current_item = item
        self.drag_source = item  # Quellelement speichern
        self.drag_start_pos = (event.x_root, event.y_root)

        # Erstelle ein transparentes Label für das Drag-Icon
        if self.drag_label:
            self.drag_label.destroy()

        # Konvertiere PIL Image zu PhotoImage
        self.current_photo = ImageTk.PhotoImage(self.ghost_image)
        self.drag_label = tk.Label(self.root, image=self.current_photo, borderwidth=0)
        self.drag_label.place(x=event.x_root, y=event.y_root)

        # Starte die Animationsschleife
        self.target_pos = (event.x_root, event.y_root)
        self.animate_drag()

    def animate_drag(self):
        """Führt die Drag-Animation aus"""
        if not self.drag_label:
            return

        current_x, current_y = self.drag_label.winfo_x(), self.drag_label.winfo_y()
        target_x, target_y = self.target_pos

        # Glättungsfaktor für die Animation
        factor = 0.3
        new_x = current_x + (target_x - current_x) * factor
        new_y = current_y + (target_y - current_y) * factor

        # Leichte Rotation basierend auf Bewegungsrichtung
        angle = math.atan2(target_y - current_y, target_x - current_x) * 180 / math.pi

        # Rotiertes Bild erstellen
        rotated_img = self.ghost_image.rotate(-angle * 0.2, expand=True, resample=Image.BICUBIC)
        self.current_photo = ImageTk.PhotoImage(rotated_img)

        self.drag_label.configure(image=self.current_photo)
        self.drag_label.image = self.current_photo  # Referenz halten
        self.drag_label.place(x=new_x, y=new_y)

        # Nächsten Animationsschritt planen
        self.animation_id = self.root.after(16, self.animate_drag)

    def update_drag(self, event):
        """Aktualisiert die Position während des Drags"""
        self.target_pos = (event.x_root, event.y_root)

    def end_drag(self):
        """Beendet den Drag-Vorgang und säubert die Animation"""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        self.current_item = None
        self.drag_source = None


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
        self.click_speed_var = tk.DoubleVar(value=0.5)  # Default click speed

        # Drag & Drop Manager
        self.drag_manager = DragManager(self)

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

        # Edit button
        ctk.CTkButton(set_frame, text="Edit Selected Set",
                      command=self.edit_selected_set).pack(pady=5, fill="x")

        # Click speed control
        speed_frame = ctk.CTkFrame(self.sidebar)
        speed_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(speed_frame, text="Click Speed (s):").pack()
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.1, to=2.0, variable=self.click_speed_var,
                                          command=self.update_click_speed)
        self.speed_slider.pack(fill="x", padx=5, pady=5)
        self.speed_display = ctk.CTkLabel(speed_frame, text=f"{self.click_speed_var.get():.1f}s")
        self.speed_display.pack()

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

    def update_click_speed(self, value):
        """Updates the click speed based on slider value"""
        global click_speed
        click_speed = float(value)
        self.speed_display.configure(text=f"{value:.1f}s")

    def create_main_content(self):
        # Sets list
        sets_frame = ctk.CTkFrame(self.main_content)
        sets_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview for sets
        self.sets_tree = ttk.Treeview(sets_frame, columns=("name", "positions", "created", "updated"), show="headings")
        self.sets_tree.heading("name", text="Set Name")
        self.sets_tree.heading("positions", text="Positions")
        self.sets_tree.heading("created", text="Created At")
        self.sets_tree.heading("updated", text="Last Updated")

        self.sets_tree.column("name", width=200)
        self.sets_tree.column("positions", width=80)
        self.sets_tree.column("created", width=150)
        self.sets_tree.column("updated", width=150)

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

        self.positions_tree.column("index", width=50, stretch=False)
        self.positions_tree.column("x", width=100, stretch=False)
        self.positions_tree.column("y", width=100, stretch=False)
        self.positions_tree.column("resolution", width=150, stretch=False)

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
        """Lädt die Sets des aktuellen Benutzers und zeigt sie an."""
        # Clear existing items
        for item in self.sets_tree.get_children():
            self.sets_tree.delete(item)

        # Load sets from database
        sets = get_user_sets(self.currently_logged_in)
        for s in sets:
            created = s["created_at"].strftime("%Y-%m-%d %H:%M")
            updated = s["updated_at"].strftime("%Y-%m-%d %H:%M")
            self.sets_tree.insert("", "end", values=(
                s["name"],
                s["positions"],
                created,
                updated
            ))

    def on_set_select(self, event):
        """Lädt die Positionen des ausgewählten Sets."""
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
        """Erstellt ein neues Set mit dem angegebenen Namen."""
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
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })

        self.load_user_sets()
        messagebox.showinfo("Success", f"Set '{set_name}' created")

    def delete_selected_set(self):
        """Löscht das ausgewählte Set."""
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

    def edit_selected_set(self):
        """Öffnet den Dialog zum Bearbeiten des ausgewählten Sets."""
        selected = self.sets_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a set to edit")
            return

        self.original_set_name = self.sets_tree.item(selected[0])["values"][0]
        if not load_positions(self.currently_logged_in, self.original_set_name):
            messagebox.showerror("Error", "Could not load selected set")
            return

        # Dialog für die Bearbeitung erstellen
        self.edit_dialog = ctk.CTkToplevel(self)
        self.edit_dialog.title(f"Edit Set: {self.original_set_name}")
        self.edit_dialog.geometry("900x650")
        self.edit_dialog.transient(self)
        self.edit_dialog.grab_set()

        # Hauptframe
        main_frame = ctk.CTkFrame(self.edit_dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Set Name Bearbeiten
        name_frame = ctk.CTkFrame(main_frame)
        name_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(name_frame, text="Set Name:").pack(side="left", padx=5)
        self.edit_name_entry = ctk.CTkEntry(name_frame)
        self.edit_name_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.edit_name_entry.insert(0, self.original_set_name)

        # Positionen Tabelle mit verbessertem Drag & Drop
        positions_frame = ctk.CTkFrame(main_frame)
        positions_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.edit_positions_tree = ttk.Treeview(positions_frame,
                                                columns=("index", "x", "y", "resolution"),
                                                show="headings")
        self.edit_positions_tree.heading("index", text="#")
        self.edit_positions_tree.heading("x", text="X")
        self.edit_positions_tree.heading("y", text="Y")
        self.edit_positions_tree.heading("resolution", text="Resolution")

        # Spaltenbreiten
        self.edit_positions_tree.column("index", width=50, stretch=False)
        self.edit_positions_tree.column("x", width=100, stretch=False)
        self.edit_positions_tree.column("y", width=100, stretch=False)
        self.edit_positions_tree.column("resolution", width=150, stretch=False)

        scrollbar = ttk.Scrollbar(positions_frame, orient="vertical",
                                  command=self.edit_positions_tree.yview)
        self.edit_positions_tree.configure(yscrollcommand=scrollbar.set)

        self.edit_positions_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Verbesserte Drag & Drop Events mit Animation
        self.edit_positions_tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.edit_positions_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.edit_positions_tree.bind("<ButtonRelease-1>", self.on_drag_release)

        # Double-Click zum Bearbeiten von Koordinaten
        self.edit_positions_tree.bind("<Double-1>", self.on_position_double_click)

        # Positionen laden
        self.update_edit_positions_display()

        # Bearbeitungs-Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        # Button zum Hinzufügen mehrerer Positionen
        add_button = ctk.CTkButton(button_frame, text="Add Multiple Positions",
                                   command=start_adding_positions)
        add_button.pack(side="left", padx=5)

        # Button zum Entfernen ausgewählter Position
        ctk.CTkButton(button_frame, text="Remove Selected",
                      command=self.remove_selected_position,
                      fg_color="#D35B58", hover_color="#C77C78").pack(side="left", padx=5)

        # Button zum Speichern der Änderungen
        ctk.CTkButton(button_frame, text="Save Changes",
                      command=self.save_set_changes).pack(side="right", padx=5)

        # Button zum Abbrechen
        ctk.CTkButton(button_frame, text="Cancel",
                      command=self.edit_dialog.destroy).pack(side="right", padx=5)

    def on_drag_start(self, event):
        """Beginnt das Drag & Drop für die Positionen."""
        item = self.edit_positions_tree.identify_row(event.y)
        if item:
            # Starte die Drag-Animation
            self.drag_manager.start_drag(event, self.edit_positions_tree, item)
            self.edit_positions_tree.selection_set(item)

    def on_drag_motion(self, event):
        """Handhabt die Bewegung während des Drag & Drop."""
        if self.drag_manager.current_item:
            # Aktualisiere die Animation
            self.drag_manager.update_drag(event)

            # Hervorhebung des aktuellen Zielelements
            target_item = self.edit_positions_tree.identify_row(event.y)
            if target_item:
                self.edit_positions_tree.selection_set(target_item)

    def on_drag_release(self, event):
        """Beendet den Drag-Vorgang und aktualisiert die Reihenfolge."""
        if self.drag_manager.current_item:
            target_item = self.edit_positions_tree.identify_row(event.y)
            if target_item and target_item != self.drag_manager.drag_source:
                try:
                    # Index der beteiligten Elemente ermitteln
                    dragged_values = self.edit_positions_tree.item(self.drag_manager.drag_source, "values")
                    target_values = self.edit_positions_tree.item(target_item, "values")

                    dragged_index = int(dragged_values[0]) - 1
                    target_index = int(target_values[0]) - 1

                    # Positionen in der Liste tauschen
                    positions[dragged_index], positions[target_index] = positions[target_index], positions[
                        dragged_index]

                    # Treeview aktualisieren
                    self.update_edit_positions_display()

                    # Auswahl wiederherstellen
                    all_items = self.edit_positions_tree.get_children()
                    if target_index < len(all_items):
                        self.edit_positions_tree.selection_set(all_items[target_index])
                except Exception as e:
                    print(f"Fehler beim Drag & Drop: {e}")

            # Aufräumen
            self.drag_manager.end_drag()

    def on_position_double_click(self, event):
        """Ermöglicht das Bearbeiten von Koordinaten durch Doppelklick."""
        region = self.edit_positions_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.edit_positions_tree.identify_column(event.x)
            item = self.edit_positions_tree.identify_row(event.y)

            if column == "#2" or column == "#3":  # X oder Y Spalte
                # Hole aktuelle Werte
                values = self.edit_positions_tree.item(item, "values")
                index = int(values[0]) - 1
                col_name = "x" if column == "#2" else "y"

                # Erstelle Eingabefeld
                x, y, width, height = self.edit_positions_tree.bbox(item, column)
                entry = ttk.Entry(self.edit_positions_tree)
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, values[1 if column == "#2" else 2])
                entry.focus()

                def save_edit(event=None):
                    try:
                        new_value = int(entry.get())
                        positions[index][col_name] = new_value
                        self.update_edit_positions_display()
                        entry.destroy()
                    except ValueError:
                        messagebox.showerror("Error", "Please enter a valid number")
                        entry.focus()

                entry.bind("<Return>", save_edit)
                entry.bind("<FocusOut>", lambda e: entry.destroy())

    def add_new_position_silent(self):
        """Fügt eine neue Position hinzu ohne Popup-Fenster."""
        # Aktuelle Mausposition holen
        x, y = pyautogui.position()
        resolution = f"{pyautogui.size().width}x{pyautogui.size().height}"
        positions.append({"x": x, "y": y, "resolution": resolution})
        self.update_edit_positions_display()
        self.edit_positions_tree.see(self.edit_positions_tree.get_children()[-1])

    def update_edit_positions_display(self):
        """Aktualisiert die Positionen-Tabelle im Bearbeitungsdialog."""
        for item in self.edit_positions_tree.get_children():
            self.edit_positions_tree.delete(item)

        for i, pos in enumerate(positions, 1):
            self.edit_positions_tree.insert("", "end", values=(
                i,
                pos["x"],
                pos["y"],
                pos["resolution"]
            ))

    def remove_selected_position(self):
        """Entfernt die ausgewählte Position aus der Liste."""
        selected = self.edit_positions_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a position to remove")
            return

        index = int(self.edit_positions_tree.item(selected[0])["values"][0]) - 1
        if 0 <= index < len(positions):
            positions.pop(index)
            self.update_edit_positions_display()

    def save_set_changes(self):
        """Speichert die Änderungen am Set direkt (ohne Kopie zu erstellen)."""
        new_name = self.edit_name_entry.get()
        if not new_name.strip():
            messagebox.showerror("Error", "Set name cannot be empty")
            return

        if self.original_set_name != new_name:
            # Prüfen ob der neue Name bereits existiert
            if positions_collection.find_one({"username": self.currently_logged_in, "set_name": new_name}):
                messagebox.showerror("Error", "A set with this name already exists")
                return

        # Set direkt aktualisieren
        if save_positions(self.currently_logged_in, new_name, update_existing=True):
            messagebox.showinfo("Success", "Changes saved successfully")
            self.edit_dialog.destroy()
            self.load_user_sets()  # Set-Liste aktualisieren
        else:
            messagebox.showerror("Error", "Failed to save changes")

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
            "created_at": datetime.now(),
            "updated_at": datetime.now()
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

        self.update_status(f"Starting in 3 seconds... Press ESC to stop. Click speed: {click_speed}s")
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
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
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