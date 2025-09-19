import pyautogui
from time import sleep
from pyjoycon import JoyCon, get_R_id, GyroTrackingJoyCon
import sys


class JoyConController:
    def __init__(self):
        pyautogui.FAILSAFE = False
        self.radius = 100
        self.move_speed = 1500
        self.circle_color = (255, 255, 0)
        self.mode = 0
        self.running = True
        self.previous_buttons = {'x': 0, 'y': 0, 'a': 0, 'b': 0, 'sr': 0, 'plus': 0}

        try:
            self.joycon, self.joycon_gyro, state_gyro = self.connect_joycon()
            self.pre_pos_x = state_gyro[0]
            self.pre_pos_y = -state_gyro[1]
        except Exception as e:
            print(f"Error initializing Joy-Con: {e}")
            sys.exit(1)

    def connect_joycon(self):
        joycon_id = get_R_id()
        joycon = JoyCon(*joycon_id)
        sleep(1)
        joycon_gyro = GyroTrackingJoyCon(*joycon_id)
        joycon_gyro.reset_orientation()
        return joycon, joycon_gyro, joycon_gyro.pointer

    def read_state(self):
        try:
            state = self.joycon.get_status()
            state_gyro = self.joycon_gyro.pointer
        except:
            state, state_gyro = None, None
        return state, state_gyro

    def process_buttons(self, state, button_callback, quit_callback, reset_callback, toggle_mode_callback):
        btn = state.get('buttons', {}).get('right', {}) if state else {}
        shared = state.get('buttons', {}).get('shared', {}) if state else {}

        def button_changed(name, source):
            return source.get(name, 0) != self.previous_buttons.get(name, 0)

        if btn:
            for name in ['x', 'a', 'y', 'b']:
                if button_changed(name, btn):
                    self.previous_buttons[name] = btn[name]
                    if btn[name]:
                        button_callback(name)

        if btn and button_changed('sr', btn):
            self.previous_buttons['sr'] = btn['sr']
            if btn['sr']:
                toggle_mode_callback()

        if shared and button_changed('plus', shared):
            self.previous_buttons['plus'] = shared['plus']
            if shared['plus']:
                reset_callback()

        if shared.get('home'):
            quit_callback()

