button_bg = "#E1E1E1"
text_bg = "#FFFFFF"
widget_fg = "#030303"
text_selectbackground = "#308CC6"
text_selectforeground = text_bg
main_bg = "#F0F0F0"


root_cfg = {"bg": main_bg}
label_cfg = {"background": main_bg,
             "foreground": widget_fg}
button_cfg = {"background": button_bg,
              "foreground": widget_fg,
              "activebackground": button_bg,
              "activeforeground": text_selectbackground}
text_cfg = {"background": text_bg,
            "foreground": widget_fg,
            "selectbackground": text_selectbackground,
            "selectforeground": text_selectforeground,
            "insertbackground": text_selectbackground}
entry_cfg = {"background": text_bg,
             "foreground": widget_fg,
             "selectbackground": text_selectbackground,
             "selectforeground": text_selectforeground,
             "insertbackground": text_selectbackground}
checkbutton_cfg = {"background": main_bg,
                   "foreground": widget_fg,
                   "activebackground": main_bg,
                   "activeforeground": widget_fg,
                   "selectcolor": main_bg}
toplevel_cfg = {"bg": main_bg}
frame_cfg = {"bg": main_bg}
option_menu_cfg = {"background": button_bg,
                   "foreground": widget_fg,
                   "activebackground": button_bg,
                   "activeforeground": text_selectbackground,
                   "highlightthickness": 0, "relief": "ridge"}
option_submenus_cfg = {"background": button_bg,
                       "foreground": widget_fg,
                       "activebackground": text_selectbackground,
                       "activeforeground": text_selectforeground}