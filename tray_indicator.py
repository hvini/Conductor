import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3


class TrayIndicator:
    def __init__(self, ui):
        self.ui = ui

    def run(self):
        indicator = AppIndicator3.Indicator.new(
            "joycon-pointer",
            "input-mouse",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()
        item_show = Gtk.MenuItem(label="Open Settings")
        item_show.connect("activate", lambda w: self.ui.root.deiconify())
        menu.append(item_show)

        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", lambda w: self.ui.quit_app())
        menu.append(item_quit)

        menu.show_all()
        indicator.set_menu(menu)
        Gtk.main()

