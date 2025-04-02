import pyautogui
import time
import keyboard
from pymongo import MongoClient
from pynput.mouse import Listener
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import customtkinter as ctk

# Verbindung zu MongoDB Atlas
MONGO_URI = "mongodb+srv://spycherelias7:ms23fzCUupdwjTeB@mousepositions.jugnj14.mongodb.net/?retryWrites=true&w=majority&appName=mousePositions"
client = MongoClient(MONGO_URI)
db = client["mouse_clicker"]
collection = db["mousePositions"]

positions = []


def save_positions(username):
    """Speichert Positionen in MongoDB unter dem Benutzernamen."""
    if positions:
        # Speichern unter dem Benutzernamen
        collection.insert_one({"username": username, "positions": positions})
        print(f"Positionen für {username} wurden in der Datenbank gespeichert!")


def load_positions(username):
    """Lädt die zuletzt gespeicherten Positionen eines Benutzers aus MongoDB."""
    global positions
    last_entry = collection.find_one({"username": username},
                                     sort=[("_id", -1)])  # Letzter gespeicherter Eintrag des Benutzers
    if last_entry:
        positions = last_entry["positions"]
        print(f"Gespeicherte Positionen für {username} geladen!")
    else:
        print(f"Keine gespeicherten Positionen für {username} gefunden.")


def on_click(x, y, button, pressed):
    """Speichert Position beim Linksklick und beendet beim Rechtsklick."""
    if pressed:
        if keyboard.is_pressed("esc"):
            print("Skript gestoppt.")
            exit()
        if str(button) == "Button.left":
            positions.append((x, y))
            print(f"Position gespeichert: {x}, {y}")
        elif str(button) == "Button.right":
            print("Erfassung abgeschlossen!")
            return False  # Beendet den Listener


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

            pyautogui.moveTo(pos[0], pos[1])  # Sofortige Bewegung
            pyautogui.click()  # Klick
            print(f"Geklickt auf: {pos}")

            time.sleep(0.5)  # 0.5 Sekunden Pause


def show_user_positions():
    """Zeigt alle gespeicherten Benutzer und deren Positionen an."""
    users = collection.distinct("username")  # Alle einzigartigen Benutzernamen abrufen
    if not users:
        print("Es gibt keine gespeicherten Benutzer.")
        return None

    print("Verfügbare Benutzer und deren Positionen:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user}")

    auswahl = input("Wähle einen Benutzer (Nummer): ")
    try:
        auswahl = int(auswahl)
        if 1 <= auswahl <= len(users):
            return users[auswahl - 1]  # Benutzername des ausgewählten Benutzers
        else:
            print("Ungültige Auswahl.")
            return None
    except ValueError:
        print("Ungültige Eingabe.")
        return None


def menu():
    """Zeigt das Konsolen-Menü an."""
    while True:
        print("\n--- Maus-Klicker Menü ---")
        print("1. Neue Positionen erfassen")
        print("2. Gespeicherte Positionen aus der Cloud laden")
        print("3. Beenden")
        auswahl = input("Wähle eine Option (1/2/3): ")

        if auswahl == "1":
            username = input("Gib deinen Benutzernamen ein: ")
            get_positions()
            save_positions(username)
            start_clicking()
        elif auswahl == "2":
            username = show_user_positions()
            if username:
                load_positions(username)
                start_clicking()
        elif auswahl == "3":
            print("Programm beendet.")
            exit()
        else:
            print("Ungültige Eingabe! Bitte 1, 2 oder 3 wählen.")


if __name__ == "__main__":
    # Configure customtkinter appearance
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


    # Set up global keyboard event handler for ESC
    def check_for_esc_key():
        global app
        if keyboard.is_pressed('esc') and hasattr(app, 'stop_operations'):
            app.stop_operations()
        app.after(100, check_for_esc_key)  # Check every 100ms


    class MouseClickerApp(ctk.CTk):
        def __init__(self):
            super().__init__()

            # Configure window
            self.title("Mouse Clicker Pro")
            self.geometry("800x600")
            self.minsize(700, 500)

            # Variables
            self.username = tk.StringVar()
            self.clickThread = None
            self.recording = False
            self.users_data = []

            # Create main frame with two columns
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=2)
            self.grid_rowconfigure(0, weight=1)

            # Left sidebar for controls
            self.sidebar = ctk.CTkFrame(self, corner_radius=0)
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            # Main content area
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            self.create_sidebar()
            self.create_main_frame()

            # Bind ESC key to stop operations
            self.bind("<Escape>", self.stop_operations)

        def create_sidebar(self):
            # App title
            self.logo_label = ctk.CTkLabel(self.sidebar, text="Mouse Clicker",
                                           font=ctk.CTkFont(size=20, weight="bold"))
            self.logo_label.pack(pady=(20, 30))

            # Username input
            username_frame = ctk.CTkFrame(self.sidebar)
            username_frame.pack(fill="x", padx=15, pady=5)

            username_label = ctk.CTkLabel(username_frame, text="Username:")
            username_label.pack(anchor="w", pady=5)

            username_entry = ctk.CTkEntry(username_frame, textvariable=self.username)
            username_entry.pack(fill="x", pady=5)

            # Action buttons
            self.record_btn = ctk.CTkButton(
                self.sidebar,
                text="Record New Positions",
                command=self.start_recording
            )
            self.record_btn.pack(fill="x", padx=15, pady=10)

            self.load_btn = ctk.CTkButton(
                self.sidebar,
                text="Load Saved Positions",
                command=self.show_users
            )
            self.load_btn.pack(fill="x", padx=15, pady=10)

            self.start_btn = ctk.CTkButton(
                self.sidebar,
                text="Start Clicking",
                command=self.start_clicking,
                state="disabled"
            )
            self.start_btn.pack(fill="x", padx=15, pady=10)

            self.stop_btn = ctk.CTkButton(
                self.sidebar,
                text="Stop",
                command=self.stop_operations,
                fg_color="#D35B58",
                hover_color="#C77C78"
            )
            self.stop_btn.pack(fill="x", padx=15, pady=10)

            # Version info
            version_label = ctk.CTkLabel(self.sidebar, text="v1.0.0")
            version_label.pack(side="bottom", pady=10)

        def create_main_frame(self):
            # Configure main frame
            self.main_frame.grid_columnconfigure(0, weight=1)
            self.main_frame.grid_rowconfigure(0, weight=0)
            self.main_frame.grid_rowconfigure(1, weight=1)

            # Status info section
            status_frame = ctk.CTkFrame(self.main_frame)
            status_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

            self.status_label = ctk.CTkLabel(
                status_frame,
                text="Ready. Choose an action from the sidebar.",
                font=ctk.CTkFont(size=14)
            )
            self.status_label.pack(pady=15)

            # Positions display
            positions_frame = ctk.CTkFrame(self.main_frame)
            positions_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            positions_frame.grid_columnconfigure(0, weight=1)
            positions_frame.grid_rowconfigure(0, weight=0)
            positions_frame.grid_rowconfigure(1, weight=1)

            positions_label = ctk.CTkLabel(
                positions_frame,
                text="Recorded Positions",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            positions_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

            # Table for positions
            self.positions_tree = ttk.Treeview(
                positions_frame,
                columns=("Index", "X", "Y"),
                show="headings"
            )

            self.positions_tree.heading("Index", text="#")
            self.positions_tree.heading("X", text="X Position")
            self.positions_tree.heading("Y", text="Y Position")

            self.positions_tree.column("Index", width=50)
            self.positions_tree.column("X", width=100)
            self.positions_tree.column("Y", width=100)

            scrollbar = ttk.Scrollbar(positions_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
            self.positions_tree.configure(yscrollcommand=scrollbar.set)

            self.positions_tree.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
            scrollbar.grid(row=1, column=1, sticky="ns", pady=15)

        def update_positions_display(self):
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)

            # Add positions to the tree view
            for i, pos in enumerate(positions):
                self.positions_tree.insert("", "end", values=(i + 1, pos[0], pos[1]))

        def start_recording(self):
            global positions

            if not self.username.get().strip():
                messagebox.showerror("Error", "Please enter a username")
                return

            positions = []  # Clear existing positions
            self.update_status("Recording positions. Click to record. Right-click to finish.")

            # Disable buttons during recording
            self.record_btn.configure(state="disabled")
            self.load_btn.configure(state="disabled")

            self.recording = True

            # Start recording in a separate thread
            threading.Thread(target=self.recording_thread, daemon=True).start()

        def recording_thread(self):
            get_positions()  # From your original code

            # Update UI after recording is done
            self.after(100, self.recording_finished)

        def recording_finished(self):
            self.recording = False
            self.update_positions_display()
            self.update_status(f"{len(positions)} positions recorded")

            # Save positions to database
            if positions:
                save_positions(self.username.get())

            # Re-enable buttons
            self.record_btn.configure(state="normal")
            self.load_btn.configure(state="normal")
            self.start_btn.configure(state="normal")

        def show_users(self):
            users = collection.distinct("username")

            if not users:
                messagebox.showinfo("Info", "No saved positions found.")
                return

            # Create a dialog to show users
            dialog = ctk.CTkToplevel(self)
            dialog.title("Saved Positions")
            dialog.geometry("400x500")
            dialog.transient(self)  # Set to be on top of the main window
            dialog.grab_set()  # Make the dialog modal

            frame = ctk.CTkFrame(dialog)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            label = ctk.CTkLabel(frame, text="Select a user:", font=ctk.CTkFont(size=16))
            label.pack(pady=10)

            # User listbox with scrollbar
            user_frame = ctk.CTkFrame(frame)
            user_frame.pack(fill="both", expand=True, padx=10, pady=10)

            scrollbar = ttk.Scrollbar(user_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(user_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 12))
            listbox.pack(side="left", fill="both", expand=True)

            scrollbar.config(command=listbox.yview)

            # Populate listbox
            for user in users:
                listbox.insert(tk.END, user)

            def on_select():
                selection = listbox.curselection()
                if selection:
                    selected_user = listbox.get(selection[0])
                    load_positions(selected_user)
                    self.username.set(selected_user)
                    self.update_positions_display()
                    # Only enable the start button if positions were actually loaded
                    if positions:
                        self.start_btn.configure(state="normal")
                        self.update_status(f"Loaded {len(positions)} positions for user {selected_user}")
                    else:
                        self.update_status(f"No positions found for user {selected_user}")
                    dialog.destroy()
                else:
                    messagebox.showwarning("Warning", "Please select a user")

            select_btn = ctk.CTkButton(frame, text="Load Selected", command=on_select)
            select_btn.pack(pady=10)

        def start_clicking(self):
            if not positions:
                messagebox.showwarning("Warning", "No positions to click")
                return

            self.update_status("Starting clicks in 3 seconds... Press ESC to stop")
            self.start_btn.configure(state="disabled")

            # Start clicking in a separate thread
            self.clickThread = threading.Thread(target=self.clicking_thread, daemon=True)
            self.clickThread.start()

        def clicking_thread(self):
            # Wait 3 seconds before starting
            time.sleep(3)

            # Use start_clicking from the original code but allow stopping
            try:
                while True:
                    if not hasattr(self, 'clickThread') or not self.clickThread:
                        break

                    for pos in positions:
                        if not hasattr(self, 'clickThread') or not self.clickThread:
                            break

                        pyautogui.moveTo(pos[0], pos[1])
                        pyautogui.click()
                        time.sleep(0.5)
            except Exception as e:
                print(f"Error in clicking thread: {e}")

        def stop_operations(self, *args):  # *args to handle event calls
            if self.recording:
                # Force stop recording
                for listener in Listener._running:
                    listener.stop()
                self.recording = False
                self.record_btn.configure(state="normal")
                self.update_status("Operations stopped")

            # Stop clicking thread if it exists
            if hasattr(self, 'clickThread') and self.clickThread:
                self.clickThread = None
                self.start_btn.configure(state="normal")
                self.update_status("Operations stopped")

        def update_status(self, message):
            self.status_label.configure(text=message)


    if __name__ == "__main__":
        app = MouseClickerApp()
        # Start the ESC key checking loop
        app.after(100, check_for_esc_key)
        app.mainloop()