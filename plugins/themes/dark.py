button_bg = "#3a3a3a"
text_bg = "#3a3a3a"
widget_fg = "#FFFFFF"
text_selectbackground = "#F0F0F0"
text_selectforeground = "#000000"
main_bg = "#2f2f31"


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