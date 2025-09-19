import tkinter as tk
from tkinter import ttk, colorchooser
import pyautogui
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk # Import Gdk for screen info

class PointerUI:
    """
    Refactored UI for Joy-Con pointer.
    Keeps radius, speed, overlay pointer.
    Allows choosing the target monitor.
    Only one color chooser button + preview.
    Only Quit button.
    """

    def __init__(self, controller):
        self.controller = controller
        self.gui_visible = False

        # --- Monitor Detection using Gdk ---
        self.monitors = self._get_monitors()
        # Fallback if Gdk fails
        if not self.monitors:
            pw, ph = pyautogui.size()
            self.monitors = [{"id": 0, "name": f"Primary: {pw}x{ph}", "x": 0, "y": 0, "width": pw, "height": ph}]
        
        initial_monitor = self.monitors[0]
        self.screen_width = initial_monitor['width']
        self.screen_height = initial_monitor['height']

        # Main window
        self.root = tk.Tk()
        self.root.title("Joy-Con Pointer — Settings")
        self.root.configure(bg="#f4f6f8")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_config)

        # ttk style
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("TLabel", background="#f4f6f8", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background="#f4f6f8")
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        self.style.configure("TCombobox", font=("Segoe UI", 10))

        # Header
        header = ttk.Label(self.root, text="Pointer Settings", font=("Segoe UI", 14, "bold"))
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 8), sticky="w")

        # Pointer settings frame
        settings = ttk.LabelFrame(self.root, text="Pointer")
        settings.grid(row=1, column=0, columnspan=2, padx=12, pady=(6, 8), sticky="ew")
        settings.columnconfigure(1, weight=1)

        self.radius_var = tk.IntVar(value=int(self.controller.radius))
        self.speed_var = tk.IntVar(value=int(self.controller.move_speed))

        self._labeled_scale(settings, "Circle radius", self.radius_var, 10, 500, row=0)
        self._labeled_scale(settings, "Move speed", self.speed_var, 100, 5000, row=1)

        # --- New: Display (Monitor) Selection Frame ---
        display_frame = ttk.LabelFrame(self.root, text="Display")
        display_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=(6, 8), sticky="ew")
        display_frame.columnconfigure(0, weight=1)

        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(
            display_frame,
            textvariable=self.monitor_var,
            values=[m['name'] for m in self.monitors],
            state="readonly"
        )
        self.monitor_combo.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.monitor_combo.current(0)
        self.monitor_combo.bind("<<ComboboxSelected>>", self._on_monitor_select)
        
        # Color frame with preview and choose color button
        color_frame = ttk.LabelFrame(self.root, text="Circle color")
        color_frame.grid(row=3, column=0, columnspan=2, padx=12, pady=(6, 8), sticky="ew")

        preview_frame = ttk.Frame(color_frame)
        preview_frame.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        self.color_preview = tk.Canvas(preview_frame, width=88, height=88,
                                       bg=self.rgb_to_hex(self.controller.circle_color),
                                       highlightthickness=1, highlightbackground="#d0d7de")
        self.color_preview.pack(pady=(4, 8))

        self.pick_btn = ttk.Button(color_frame, text="Choose color…", command=self._pick_color)
        self.pick_btn.grid(row=0, column=1, padx=12, pady=12, sticky="e")

        # Quit button only
        actions = ttk.Frame(self.root)
        actions.grid(row=4, column=0, columnspan=2, padx=12, pady=(10, 12), sticky="ew")
        actions.columnconfigure(0, weight=1)

        self.quit_btn = ttk.Button(actions, text="Quit", command=self.quit_app)
        self.quit_btn.grid(row=0, column=0, sticky="ew")

        # Keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self.hide_config())
        self.root.bind("<Control-q>", lambda e: self.quit_app())

        # Overlay pointer window
        self.pointer_win = tk.Toplevel(self.root)
        self.pointer_win.overrideredirect(True)
        self.pointer_win.attributes("-topmost", 1)
        self.pointer_win.wm_attributes("-alpha", 0)
        self.pointer_win.withdraw()
        
        self.canvas = tk.Canvas(self.pointer_win, width=self.screen_width,
                                height=self.screen_height, highlightthickness=0, bg="#000000")
        self.canvas.pack(fill="both", expand=True)

        # Set initial overlay geometry for the first monitor
        self._update_overlay_geometry(0)

        # initial pointer circle
        x, y = pyautogui.position()
        # Adjust for the origin of the initial monitor
        x -= initial_monitor['x']
        y -= initial_monitor['y']
        
        r = int(self.controller.radius)
        color_hex = self.rgb_to_hex(self.controller.circle_color)
        self.circle = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                              fill=color_hex, outline="")

    # ---- helpers ----
    def _get_monitors(self):
        """Uses Gdk to get information about all connected monitors."""
        monitors = []
        try:
            screen = Gdk.Screen.get_default()
            n_monitors = screen.get_n_monitors()
            for i in range(n_monitors):
                geom = screen.get_monitor_geometry(i)
                monitors.append({
                    "id": i,
                    "name": f"Monitor {i+1}: {geom.width}x{geom.height} at ({geom.x},{geom.y})",
                    "x": geom.x,
                    "y": geom.y,
                    "width": geom.width,
                    "height": geom.height
                })
        except Exception as e:
            print(f"Could not get monitor info via Gdk: {e}")
        return monitors

    def _update_overlay_geometry(self, monitor_index):
        """Moves and resizes the overlay window to the selected monitor."""
        if not (0 <= monitor_index < len(self.monitors)):
            return
        
        monitor = self.monitors[monitor_index]
        x, y, w, h = monitor["x"], monitor["y"], monitor["width"], monitor["height"]

        # Update the overlay window's position and size
        self.pointer_win.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas.config(width=w, height=h)

        # Store current dimensions for coordinate calculations
        self.screen_width = w
        self.screen_height = h
        self.controller.active_monitor_geom = (x, y) # Pass geometry to controller

    def _on_monitor_select(self, event=None):
        """Handles the monitor selection event from the combobox."""
        selected_index = self.monitor_combo.current()
        self._update_overlay_geometry(selected_index)

    def _labeled_scale(self, parent, label, var, frm, to, row=0):
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=(8, 6), pady=6)

        scale = tk.Scale(parent, from_=frm, to=to, orient="horizontal",
                         variable=var, length=220, showvalue=True)
        scale.grid(row=row, column=1, sticky="ew", padx=(6, 8), pady=6)

    def rgb_to_hex(self, rgb):
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        return f"#{r:02x}{g:02x}{b:02x}"

    def _pick_color(self):
        picked = colorchooser.askcolor(parent=self.root)
        if picked[1]:
            r, g, b = map(int, picked[0])
            self.controller.circle_color = (r, g, b)
            self.color_preview.config(bg=picked[1])
            self.canvas.itemconfig(self.circle, fill=picked[1])

    # ---- public API ----
    def hide_config(self):
        self.root.withdraw()

    def quit_app(self):
        self.controller.running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        try:
            self.pointer_win.destroy()
        except Exception:
            pass
        try:
            Gtk.main_quit()
        except Exception:
            pass

    def update_ui_from_controller(self):
        """Push UI values into controller and refresh overlay visuals."""
        self.controller.radius = int(self.radius_var.get())
        self.controller.move_speed = int(self.speed_var.get())
        try:
            self.canvas.itemconfig(self.circle, fill=self.rgb_to_hex(self.controller.circle_color))
            self.color_preview.config(bg=self.rgb_to_hex(self.controller.circle_color))
        except Exception:
            pass
