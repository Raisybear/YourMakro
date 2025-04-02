# YourMakro

YourMakro ist ein leistungsstarkes, benutzerfreundliches Makro-Tool, das es ermöglicht, Mauspositionen aufzuzeichnen und automatisch auszuführen. Die Positionen werden in einer **MongoDB-Cloud-Datenbank** gespeichert, sodass sie jederzeit abgerufen und wiederverwendet werden können.

## 🚀 Funktionen
- **Mauspositionen aufzeichnen** und speichern
- **Automatisches Klicken** an gespeicherten Positionen
- **Benutzerverwaltung** zur Speicherung individueller Makros
- **GUI mit CustomTkinter** für einfache Bedienung
- **ESC-Taste als Notfall-Stop**

## 🛠️ Technologien
- **Python** (Hauptsprache)
- **PyAutoGUI** (Automatisierung)
- **Pynput** (Maus-Listener)
- **Keyboard** (Hotkey-Erkennung)
- **MongoDB Atlas** (Cloud-Datenbank)
- **Tkinter & CustomTkinter** (GUI)

## 📦 Installation
### Voraussetzungen
- Python 3.x installiert
- Abhängigkeiten mit folgendem Befehl installieren:
  ```sh
  pip install pyautogui keyboard pymongo pynput customtkinter
  ```

## 🚀 Nutzung
1. **Starte die Anwendung:**
   ```sh
   python yourmakro.py
   ```
2. **Wähle eine der Optionen:**
   - Positionen aufzeichnen
   - Gespeicherte Positionen laden
   - Automatisches Klicken starten
3. **Beende das Skript jederzeit mit `ESC`.**

## 🖥️ GUI-Beschreibung
- **Username eingeben** → Um deine Positionen zu speichern
- **"Record New Positions"** → Aufzeichnen neuer Positionen
- **"Load Saved Positions"** → Geladene Positionen anzeigen
- **"Start Clicking"** → Automatische Klick-Sequenz starten
- **"Stop"** → Vorgang jederzeit stoppen

## 📸 Screenshots
*(Hier können Screenshots der Anwendung hinzugefügt werden)*

## 📜 Lizenz
Dieses Projekt steht unter der MIT-Lizenz.

## 👤 Autor
Entwickelt von **Elias Spycher**. Bei Fragen oder Anregungen gerne kontaktieren! 🚀

