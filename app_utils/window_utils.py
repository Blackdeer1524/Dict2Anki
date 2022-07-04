from tkinter import StringVar, OptionMenu


def spawn_toplevel_in_center(master, toplevel_widget, desired_toplevel_width=0, desired_toplevel_height=0):
    def get_center_spawn_conf():
        """
        :param master: master of placing widget
        :param placing_widget_width: current window width
        :param placing_widget_height: current window height
        :return: widget spawn conf
        """
        nonlocal master, width, height
        # получение координат на экране через self.winfo_rootx(), self.winfo_rooty() даёт некоторое смещение
        master_size, master_position_on_screen_x, master_position_on_screen_y = master.winfo_geometry().split(sep="+")
        master_width, master_height = master_size.split(sep="x")
        master_window_center_x = int(master_position_on_screen_x) + int(master_width) // 2
        master_window_center_y = int(master_position_on_screen_y) + int(master_height) // 2
        window_size = f"{width}x{height}"
        spawn_cords = f"+{master_window_center_x - width // 2}+{master_window_center_y - height // 2}"
        return window_size + spawn_cords

    toplevel_widget.update()
    width = desired_toplevel_width if desired_toplevel_width else toplevel_widget.winfo_width()
    height = desired_toplevel_height if desired_toplevel_height else toplevel_widget.winfo_height()
    toplevel_widget.geometry(get_center_spawn_conf())


def get_option_menu(master, init_text, values, command, option_menu_cfg=None, option_submenu_cfg=None):
    if option_menu_cfg is None:
        option_menu_cfg = {}
    if option_submenu_cfg is None:
        option_submenu_cfg = {}

    var = StringVar()
    var.set(init_text)
    option_menu = OptionMenu(master, var, *values, command=command)
    option_menu.configure(**option_menu_cfg)
    for submenu_index in range(len(values)):
        option_menu["menu"].entryconfig(submenu_index, **option_submenu_cfg)
    return option_menu
