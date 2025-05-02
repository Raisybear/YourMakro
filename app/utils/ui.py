import math
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
from tkinter import messagebox


def create_drag_icon():
    """Create a drag icon with Pillow."""
    img = Image.new('RGBA', (100, 40), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background with rounded corners
    draw.rounded_rectangle([(0, 0), (100, 40)], 15, fill=(70, 130, 180, 200))

    # Text and arrows
    draw.text((20, 10), "Drag", fill=(255, 255, 255, 255))
    draw.line([(70, 15), (85, 15), (80, 10)], fill=(255, 255, 255), width=2)
    draw.line([(70, 25), (85, 25), (80, 30)], fill=(255, 255, 255), width=2)

    return img


class DragManager:
    """Manage drag and drop animations."""

    def __init__(self, root):
        self.root = root
        self.drag_label = None
        self.drag_start_pos = (0, 0)
        self.current_item = None
        self.ghost_image = create_drag_icon()
        self.animation_id = None
        self.target_pos = (0, 0)
        self.drag_source = None

    def start_drag(self, event, tree, item):
        """Start drag operation."""
        self.current_item = item
        self.drag_source = item
        self.drag_start_pos = (event.x_root, event.y_root)

        if self.drag_label:
            self.drag_label.destroy()

        self.current_photo = ImageTk.PhotoImage(self.ghost_image)
        self.drag_label = tk.Label(self.root, image=self.current_photo, borderwidth=0)
        self.drag_label.place(x=event.x_root, y=event.y_root)

        self.target_pos = (event.x_root, event.y_root)
        self.animate_drag()

    def animate_drag(self):
        """Animate drag operation."""
        if not self.drag_label:
            return

        current_x, current_y = self.drag_label.winfo_x(), self.drag_label.winfo_y()
        target_x, target_y = self.target_pos

        factor = 0.3
        new_x = current_x + (target_x - current_x) * factor
        new_y = current_y + (target_y - current_y) * factor

        angle = math.atan2(target_y - current_y, target_x - current_x) * 180 / math.pi
        rotated_img = self.ghost_image.rotate(-angle * 0.2, expand=True, resample=Image.BICUBIC)
        self.current_photo = ImageTk.PhotoImage(rotated_img)

        self.drag_label.configure(image=self.current_photo)
        self.drag_label.image = self.current_photo
        self.drag_label.place(x=new_x, y=new_y)

        self.animation_id = self.root.after(16, self.animate_drag)

    def update_drag(self, event):
        """Update drag position."""
        self.target_pos = (event.x_root, event.y_root)

    def end_drag(self):
        """End drag operation."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        self.current_item = None
        self.drag_source = None


def show_message(title, message, error=False):
    """Show a message dialog."""
    if error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)


def confirm_dialog(title, message):
    """Show a confirmation dialog and return result."""
    return messagebox.askyesno(title, message)


def format_datetime(dt):
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M")


def configure_treeview_style(style):
    """Configure ttk treeview style."""
    style.configure("Treeview",
                   background="#f0f0f0",
                   foreground="black",
                   rowheight=25,
                   fieldbackground="#f0f0f0")
    style.map('Treeview',
             background=[('selected', '#4a6984')],
             foreground=[('selected', 'white')])