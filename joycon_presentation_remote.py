import tkinter as tk
import pyautogui
from time import sleep
from pyjoycon import JoyCon, get_R_id, GyroTrackingJoyCon
import sys

class JoyConPointerApp:
    RADIUS = 200
    MOVE_SPEED = 1500
    ALPHA_BACKGROUND = 0.7
    ALPHA_HIGHLIGHT = 0.3

    def __init__(self):
        pyautogui.FAILSAFE = False
        self.mode = 0
        self.gui_visible = False
        self.previous_buttons = {
            'x': 0, 'y': 0, 'a': 0, 'b': 0,
            'sr': 0, 'plus': 0
        }

        try:
            self.joycon, self.joycon_gyro, state_gyro = self.connect_joycon()
            self.pre_pos_x = state_gyro[0]
            self.pre_pos_y = -state_gyro[1]
        except Exception as e:
            print(f"Error initializing Joy-Con: {e}")
            sys.exit(1)

        self.screen_width, self.screen_height = pyautogui.size()
        self.init_gui()

    def connect_joycon(self):
        joycon_id = get_R_id()
        joycon = JoyCon(*joycon_id)
        sleep(1)
        joycon_gyro = GyroTrackingJoyCon(*joycon_id)
        joycon_gyro.reset_orientation()
        return joycon, joycon_gyro, joycon_gyro.pointer

    def init_gui(self):
        tk.Canvas.create_circle = lambda s, x, y, r, **kwargs: s.create_oval(x - r, y - r, x + r, y + r, **kwargs)
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=self.screen_width, height=self.screen_height,
                                highlightthickness=0, bg='#000000')
        self.canvas.pack()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', 1)
        self.root.wm_attributes('-alpha', 0)
        self.root.withdraw()

        x, y = pyautogui.position()
        self.circle = self.canvas.create_oval(
            x - self.RADIUS, y - self.RADIUS, x + self.RADIUS, y + self.RADIUS,
            fill='yellow', outline=''
        )

    def update(self):
        try:
            state = self.joycon.get_status()
            state_gyro = self.joycon_gyro.pointer
        except Exception as e:
            print(f"Error reading Joy-Con state: {e}")
            state_gyro = None

        if not state_gyro:
            print("Gyro disconnected. Attempting reconnect...")
            try:
                self.joycon, self.joycon_gyro, state_gyro = self.connect_joycon()
                print("Reconnected Joy-Con.")
            except Exception as e:
                print(f"Reconnect failed: {e}")
                self.canvas.after(1000, self.update)
                return

        cur_pos_x = state_gyro[0]
        cur_pos_y = -state_gyro[1]
        move_x = cur_pos_x - self.pre_pos_x
        move_y = cur_pos_y - self.pre_pos_y
        self.pre_pos_x, self.pre_pos_y = cur_pos_x, cur_pos_y

        # Handle Joy-Con buttons
        btn = state['buttons']['right']
        shared = state['buttons']['shared']

        def button_changed(name):
            return btn.get(name, 0) != self.previous_buttons.get(name, 0)

        for name in ['x', 'y', 'a', 'b']:
            if button_changed(name):
                self.previous_buttons[name] = btn[name]
                if btn[name]:
                    pyautogui.press('pageup' if name == 'x' else
                                    'pagedown' if name == 'b' else None)
                    if name in ('a', 'y'):
                        pyautogui.click()

        if button_changed('sr'):
            self.previous_buttons['sr'] = btn['sr']
            if btn['sr']:
                self.mode = 0 if self.mode else 1

        if button_changed('plus'):
            self.previous_buttons['plus'] = shared['plus']
            if shared['plus']:
                self.joycon_gyro.reset_orientation()

        if shared.get('home'):
            print("Home button pressed. Exiting.")
            self.root.destroy()
            return

        # Show or hide GUI
        if btn.get('r') or btn.get('zr'):
            dx = int(max(-32768, min(32767, move_x * self.MOVE_SPEED)))
            dy = int(max(-32768, min(32767, move_y * self.MOVE_SPEED)))
            pyautogui.moveRel(dx, dy, _pause=False)

            if not self.gui_visible:
                self.root.deiconify()
                self.root.lift()
                self.gui_visible = True

            alpha = self.ALPHA_BACKGROUND if self.mode == 0 else self.ALPHA_HIGHLIGHT
            self.root.wm_attributes('-alpha', alpha)
            self.canvas.itemconfig(self.circle, fill='yellow')
            x, y = pyautogui.position()
            self.canvas.coords(self.circle, x - self.RADIUS, y - self.RADIUS,
                               x + self.RADIUS, y + self.RADIUS)
        else:
            if self.gui_visible:
                self.root.wm_attributes('-alpha', 0)
                self.root.withdraw()
                self.gui_visible = False

        self.canvas.after(10, self.update)

    def run(self):
        print("Joy-Con presentation remote ready!")
        print("Press 'R' or 'ZR' on Joy-Con to show pointer.")
        print("Press Home to exit.")
        self.canvas.after(10, self.update)
        self.root.mainloop()

if __name__ == '__main__':
    JoyConPointerApp().run()

