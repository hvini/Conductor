import threading
import pyautogui
from joycon_controller import JoyConController
from pointer_ui import PointerUI
from tray_indicator import TrayIndicator


class JoyConPointerApp:
    def __init__(self):
        self.controller = JoyConController()
        self.ui = PointerUI(self.controller)
        self.tray = TrayIndicator(self.ui)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def run(self):
        self.ui.pointer_win.after(10, self.update)
        print("Joy-Con pointer ready!")
        self.ui.root.mainloop()

    def update(self):
        if not self.controller.running:
            return

        state, state_gyro = self.controller.read_state()
        if not state_gyro:
            self.ui.pointer_win.after(1000, self.update)
            return

        # process buttons
        self.controller.process_buttons(
            state,
            button_callback=self.handle_button,
            quit_callback=self.ui.quit_app,
            reset_callback=self.controller.joycon_gyro.reset_orientation,
            toggle_mode_callback=self.toggle_mode
        )

        # atualizar parâmetros
        self.ui.update_ui_from_controller()

        # mover ponteiro
        cur_pos_x, cur_pos_y = state_gyro[0], -state_gyro[1]
        move_x = cur_pos_x - self.controller.pre_pos_x
        move_y = cur_pos_y - self.controller.pre_pos_y
        self.controller.pre_pos_x, self.controller.pre_pos_y = cur_pos_x, cur_pos_y

        btn = state.get('buttons', {}).get('right', {}) if state else {}
        if btn and (btn.get('r') or btn.get('zr')):
            dx = int(move_x * self.controller.move_speed)
            dy = int(move_y * self.controller.move_speed)

            # Clamp to 16-bit signed range
            dx = max(-32768, min(32767, dx))
            dy = max(-32768, min(32767, dy))

            pyautogui.moveRel(dx, dy, _pause=False)

            if not self.ui.gui_visible:
                self.ui.pointer_win.deiconify()
                self.ui.pointer_win.lift()
                self.ui.gui_visible = True

            alpha = 0.7 if self.controller.mode == 0 else 0.3
            self.ui.pointer_win.wm_attributes('-alpha', alpha)
            x, y = pyautogui.position()
            self.ui.canvas.coords(self.ui.circle, x - self.controller.radius, y - self.controller.radius,
                                  x + self.controller.radius, y + self.controller.radius)
        else:
            if self.ui.gui_visible:
                self.ui.pointer_win.wm_attributes('-alpha', 0)
                self.ui.pointer_win.withdraw()
                self.ui.gui_visible = False

        self.ui.pointer_win.after(10, self.update)

    def handle_button(self, name):
        if name == 'x':
            self.ui.hide_config()
        elif name == 'b':
            pyautogui.press('pagedown')
        elif name in ('a', 'y'):
            pyautogui.click()

    def toggle_mode(self):
        self.controller.mode = 0 if self.controller.mode == 1 else 1


if __name__ == "__main__":
    app = JoyConPointerApp()
    app.run()

