import json
import re
import webbrowser
from datetime import datetime
from functools import partial
from tkinter import BooleanVar
from tkinter import Button, Menu
from tkinter import Frame
from tkinter import Label
from tkinter import Toplevel
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from typing import Any
from typing import Callable

from playsound import playsound
from tkinterdnd2 import Tk

from plugins_management.containers import LanguagePackageContainter
from consts.card_fields import FIELDS
from consts.paths import *
from plugins_management.factory import loaded_plugins
from utils.audio_utils import AudioDownloader
from utils.cards import Card
from utils.cards import Deck, SentenceFetcher, SavedDataDeck, CardStatus
from utils.error_handling import create_exception_message
from utils.error_handling import error_handler
from utils.global_bindings import Binder
from utils.image_utils import ImageSearch
from utils.search_checker import ParsingException
from utils.search_checker import get_card_filter
from utils.storages import validate_json
from utils.string_utils import remove_special_chars
from utils.widgets import EntryWithPlaceholder as Entry
from utils.widgets import ScrolledFrame
from utils.widgets import TextWithPlaceholder as Text
from utils.window_utils import get_option_menu
from utils.window_utils import spawn_toplevel_in_center


class App(Tk):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        if not os.path.exists("./temp/"):
            os.makedirs("./temp")

        if not os.path.exists(LOCAL_MEDIA_DIR):
            os.makedirs(LOCAL_MEDIA_DIR)

        if not os.path.exists("./Cards/"):
            os.makedirs("./Cards")

        if not os.path.exists("./Words/"):
            os.makedirs("./Words")

        if not os.path.exists("./Words/custom.json"):
            with open("./Words/custom.json", "w", encoding="UTF-8") as custom_file:
                json.dump([], custom_file)

        self.configurations, self.lang_pack, error_code = self.load_conf_file()
        if error_code:
            self.destroy()
            return
        self.save_conf_file()
        self.history = App.load_history_file()

        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
        self.session_start = datetime.now()
        self.str_session_start = self.session_start.strftime("%d-%m-%Y-%H-%M-%S")

        if not self.history.get(self.configurations["directories"]["last_open_file"]):
            self.history[self.configurations["directories"]["last_open_file"]] = 0

        self.theme = loaded_plugins.get_theme(self.configurations["app"]["theme"])
        self.configure(**self.theme.root_cfg)
        self.Label    = partial(Label,    **self.theme.label_cfg)
        self.Button   = partial(Button,   **self.theme.button_cfg)
        self.Text     = partial(Text,     **self.theme.text_cfg)
        self.Entry    = partial(Entry,    **self.theme.entry_cfg)
        self.Toplevel = partial(Toplevel, **self.theme.toplevel_cfg)
        self.Frame    = partial(Frame,    **self.theme.frame_cfg)
        self.get_option_menu = partial(get_option_menu,
                                       option_menu_cfg=self.theme.option_menu_cfg,
                                       option_submenu_cfg=self.theme.option_submenus_cfg)

        wp_name = self.configurations["scrappers"]["word_parser_name"]
        if (wp_type := self.configurations["scrappers"]["word_parser_type"]) == "web":
            self.cd = loaded_plugins.get_web_card_generator(wp_name)
        elif wp_type == "local":
            self.cd = loaded_plugins.get_local_card_generator(wp_name)
        else:
            raise NotImplemented("Unknown word_parser_type: {}!".format(self.configurations["scrappers"]["word_parser_type"]))
        self.typed_word_parser_name = f"[{wp_type}] {wp_name}"

        self.deck = Deck(deck_path=self.configurations["directories"]["last_open_file"],
                         current_deck_pointer=self.history[self.configurations["directories"]["last_open_file"]],
                         card_generator=self.cd)

        self.card_processor = loaded_plugins.get_card_processor("Anki")
        self.dict_card_data: dict = {}
        self.sentence_batch_size = 5
        self.sentence_parser = loaded_plugins.get_sentence_parser(self.configurations["scrappers"]["base_sentence_parser"])
        self.sentence_fetcher = SentenceFetcher(sent_fetcher=self.sentence_parser.get_sentence_batch,
                                                sentence_batch_size=self.sentence_batch_size)

        self.image_parser = loaded_plugins.get_image_parser(self.configurations["scrappers"]["base_image_parser"])

        if (local_audio_getter_name := self.configurations["scrappers"]["local_audio"]):
            self.local_audio_getter = loaded_plugins.get_local_audio_getter(local_audio_getter_name)
        else:
            self.local_audio_getter = None

        self.saved_cards_data = SavedDataDeck()
        self.deck_saver = loaded_plugins.get_deck_saving_formats(self.configurations["deck_saving_format"])
        self.audio_saver = loaded_plugins.get_deck_saving_formats("json_deck_audio")
        self.buried_saver = loaded_plugins.get_deck_saving_formats("json_deck_cards")

        main_menu = Menu(self)
        filemenu = Menu(main_menu, tearoff=0)
        filemenu.add_command(label=self.lang_pack.create_file_menu_label, command=self.create_file_dialog)
        filemenu.add_command(label=self.lang_pack.open_file_menu_label, command=self.change_file)
        filemenu.add_command(label=self.lang_pack.save_files_menu_label, command=self.save_button)
        filemenu.add_separator()

        help_menu = Menu(filemenu, tearoff=0)
        help_menu.add_command(label=self.lang_pack.hotkeys_and_buttons_help_menu_label, command=self.help_command)
        help_menu.add_command(label=self.lang_pack.query_language_menu_label, command=self.get_query_language_help)
        filemenu.add_cascade(label=self.lang_pack.help_master_menu_label, menu=help_menu)

        filemenu.add_separator()
        filemenu.add_command(label=self.lang_pack.download_audio_menu_label, 
                             command=partial(self.download_audio, choose_file=True))
        filemenu.add_separator()
        filemenu.add_command(label=self.lang_pack.change_media_folder_menu_label, command=self.change_media_dir)
        main_menu.add_cascade(label=self.lang_pack.file_master_menu_label, menu=filemenu)

        main_menu.add_command(label=self.lang_pack.add_card_menu_label, command=self.add_word_dialog)
        main_menu.add_command(label=self.lang_pack.search_inside_deck_menu_label, command=self.find_dialog)
        main_menu.add_command(label=self.lang_pack.statistics_menu_label, command=self.statistics_dialog)
        main_menu.add_command(label=self.lang_pack.themes_menu_label, command=self.change_theme)
        main_menu.add_command(label=self.lang_pack.language_menu_label, command=self.change_language)
        main_menu.add_command(label=self.lang_pack.anki_config_menu_label, command=self.anki_dialog)
        main_menu.add_command(label=self.lang_pack.exit_menu_label, command=self.on_closing)
        self.config(menu=main_menu)

        self.browse_button = self.Button(self,
                                         text=self.lang_pack.browse_button_text,
                                         command=self.web_search_command)
        self.configure_word_parser_button = self.Button(self,
                                                        text=self.lang_pack.configure_word_parser_button_text,
                                                        command=self.configure_dictionary)
        self.find_image_button = self.Button(self,
                                             text=self.lang_pack.find_image_button_normal_text,
                                             command=self.start_image_search)
        self.image_word_parsers_names = loaded_plugins.image_parsers.loaded

        self.image_parser_option_menu = self.get_option_menu(self,
                                                             init_text=self.image_parser.name,
                                                             values=self.image_word_parsers_names,
                                                             command=lambda parser_name:
                                                             self.change_image_parser(parser_name))
        self.sentence_button_text = self.lang_pack.sentence_button_text
        self.add_sentences_button = self.Button(self,
                                                text=self.sentence_button_text,
                                                command=self.replace_sentences)

        self.sentence_parser_option_menu = self.get_option_menu(self,
                                                                init_text=self.sentence_parser.name,
                                                                values=loaded_plugins.web_sent_parsers.loaded,
                                                                command=lambda parser_name:
                                                                self.change_sentence_parser(parser_name))

        self.word_text = self.Text(self, placeholder=self.lang_pack.word_text_placeholder, height=2)
        self.alt_terms_field = self.Text(self, relief="ridge", state="disabled", height=1)
        self.definition_text = self.Text(self, placeholder=self.lang_pack.definition_text_placeholder)

        self.sent_text_list = []
        self.sent_button_list = []
        button_width = 3
        for i in range(5):
            self.sent_text_list.append(
                self.Text(self, placeholder=f"{self.lang_pack.sentence_text_placeholder_prefix} {i + 1}"))
            self.sent_text_list[-1].fill_placeholder()
            self.sent_button_list.append(self.Button(self,
                                                text=f"{i + 1}",
                                                command=lambda x=i: self.choose_sentence(x),
                                                width=button_width))

        self.skip_button = self.Button(self,
                                       text=self.lang_pack.skip_button_text,
                                       command=self.skip_command,
                                       width=button_width)
        self.prev_button = self.Button(self,
                                       text=self.lang_pack.prev_button_text,
                                       command=lambda x=-1: self.replace_decks_pointers(x),
                                       state="disabled", width=button_width)
        self.sound_button = self.Button(self,
                                        text=self.lang_pack.sound_button_text,
                                        command=self.play_sound,
                                        width=button_width)
        self.anki_button = self.Button(self,
                                       text=self.lang_pack.anki_button_text,
                                       command=self.open_anki_browser,
                                       width=button_width)
        self.bury_button = self.Button(self,
                                       text=self.lang_pack.bury_button_text,
                                       command=self.bury_command,
                                       width=button_width)

        self.user_tags_field = self.Entry(self,
                                          placeholder=self.lang_pack.user_tags_field_placeholder)
        self.user_tags_field.fill_placeholder()

        self.tag_prefix_field = self.Entry(self, justify="center", width=8)
        self.tag_prefix_field.insert(0, self.configurations["tags_hierarchical_pref"])
        self.dict_tags_field = self.Text(self, relief="ridge", state="disabled", height=2)

        Text_padx = 10
        Text_pady = 2
        self.browse_button.grid(row=0, column=0, padx=(Text_padx, 0), pady=(Text_pady, 0), sticky="news", columnspan=4)
        self.configure_word_parser_button.grid(row=0, column=4, padx=(0, Text_padx), pady=(Text_pady, 0),
                                            columnspan=4, sticky="news")

        self.word_text.grid(row=1, column=0, padx=Text_padx, pady=Text_pady, columnspan=8, sticky="news")

        self.alt_terms_field.grid(row=2, column=0, padx=Text_padx, columnspan=8, sticky="news")

        self.find_image_button.grid(row=3, column=0, padx=(Text_padx, 0), pady=Text_pady, sticky="news", columnspan=4)
        self.image_parser_option_menu.grid(row=3, column=4, padx=(0, Text_padx), pady=Text_pady, columnspan=4,
                                           sticky="news")

        self.definition_text.grid(row=4, column=0, padx=Text_padx, columnspan=8, sticky="news")

        self.add_sentences_button.grid(row=5, column=0, padx=(Text_padx, 0), pady=Text_pady, sticky="news", columnspan=4)
        self.sentence_parser_option_menu.grid(row=5, column=4, padx=(0, Text_padx), pady=Text_pady, columnspan=4,
                                              sticky="news")

        for i in range(5):
            c_pady = Text_pady if i % 2 else 0
            self.sent_text_list[i].grid(row=6 + i, column=0, columnspan=6, padx=Text_padx, pady=c_pady, sticky="news")
            self.sent_button_list[i].grid(row=6 + i, column=6, padx=0, pady=c_pady, sticky="ns")

        self.skip_button.grid(row=6, column=7, padx=Text_padx, pady=0, sticky="ns")
        self.prev_button.grid(row=7, column=7, padx=Text_padx, pady=Text_pady, sticky="ns")
        self.sound_button.grid(row=8, column=7, padx=Text_padx, pady=0, sticky="ns")
        self.anki_button.grid(row=9, column=7, padx=Text_padx, pady=Text_pady, sticky="ns")
        self.bury_button.grid(row=10, column=7, padx=Text_padx, pady=0, sticky="ns")

        self.user_tags_field.grid(row=11, column=0, padx=Text_padx, pady=Text_pady, columnspan=6,
                                  sticky="news")
        self.tag_prefix_field.grid(row=11, column=6, padx=(0, Text_padx), pady=Text_pady, columnspan=2,
                                   sticky="news")
        self.dict_tags_field.grid(row=12, column=0, padx=Text_padx, pady=(0, Text_padx), columnspan=8,
                                  sticky="news")
        for i in range(6):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_rowconfigure(7, weight=1)
        self.grid_rowconfigure(8, weight=1)
        self.grid_rowconfigure(9, weight=1)
        self.grid_rowconfigure(10, weight=1)

        def focus_next_window(event):
            event.widget.tk_focusNext().focus()
            return "break"

        def focus_prev_window(event):
            event.widget.tk_focusPrev().focus()
            return "break"

        self.new_order = [self.browse_button, self.word_text, self.find_image_button, self.definition_text,
                          self.add_sentences_button] + self.sent_text_list + \
                         [self.user_tags_field] + self.sent_button_list + [self.skip_button, self.prev_button,
                                                                       self.anki_button, self.bury_button,
                                                                       self.tag_prefix_field]

        for widget_index in range(len(self.new_order)):
            self.new_order[widget_index].lift()
            self.new_order[widget_index].bind("<Tab>", focus_next_window)
            self.new_order[widget_index].bind("<Shift-Tab>", focus_prev_window)

        self.bind("<Escape>", lambda event: self.on_closing())
        self.bind("<Control-Key-0>", lambda event: self.geometry("+0+0"))
        self.bind("<Control-d>", lambda event: self.skip_command())
        self.bind("<Control-q>", lambda event: self.bury_command())
        self.bind("<Control-s>", lambda event: self.save_button())
        self.bind("<Control-f>", lambda event: self.find_dialog())
        self.bind("<Control-e>", lambda event: self.statistics_dialog())
        self.bind("<Control-Shift_L><A>", lambda event: self.add_word_dialog())
        self.bind("<Control-z>", lambda event: self.replace_decks_pointers(-1))
        self.bind("<Control-Key-1>", lambda event: self.choose_sentence(0))
        self.bind("<Control-Key-2>", lambda event: self.choose_sentence(1))
        self.bind("<Control-Key-3>", lambda event: self.choose_sentence(2))
        self.bind("<Control-Key-4>", lambda event: self.choose_sentence(3))
        self.bind("<Control-Key-5>", lambda event: self.choose_sentence(4))

        self.gb = Binder()
        self.gb.bind("Control", "c", "space",
                     action=lambda: self.define_word(word_query=self.clipboard_get(), additional_query="")
                     )
        self.gb.start()

        self.minsize(500, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.refresh()
        self.geometry(self.configurations["app"]["main_window_geometry"])
        self.configure()

    def show_window(self, title: str, text: str) -> Toplevel:
        text_toplevel = self.Toplevel(self)
        text_toplevel.title(title)
        message_display_text = self.Text(text_toplevel, **self.theme.label_cfg)
        message_display_text.insert(1.0, text)
        message_display_text["state"] = "disabled"
        message_display_text.pack(expand=1, fill="both")
        message_display_text.update()
        text_toplevel.config(width=min(1000, message_display_text.winfo_width()),
                             height=min(500, message_display_text.winfo_height()))
        text_toplevel.bind("<Escape>", lambda event: text_toplevel.destroy())
        return text_toplevel

    def show_errors(self, *args, **kwargs) -> None:
        error_log = create_exception_message()
        self.clipboard_clear()
        self.clipboard_append(error_log)
        error_toplevel = self.show_window(title=self.lang_pack.error_title, text=error_log)
        error_toplevel.grab_set()

    @error_handler(show_errors)
    def save_conf_file(self):
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(self.configurations, f, indent=3)

    def load_conf_file(self) -> tuple[dict[str, dict], LanguagePackageContainter, bool]:
        standard_conf_file = {"app": {"theme": "dark",
                                      "main_window_geometry": "500x800+0+0",
                                      "image_search_position": "+0+0",
                                      "language_package": "eng"},
                              "card_processor": "Anki",
                              "deck_saving_format": "csv",
                              "scrappers": {"base_sentence_parser": "sentencedict",
                                            "word_parser_type": "web",
                                            "word_parser_name": "cambridge_US",
                                            "base_image_parser": "google",
                                            "local_audio": ""},
                              "tags_hierarchical_pref": "",
                              "directories": {"media_dir": "",
                                              "last_open_file": "",
                                              "last_save_dir": ""},
                              "anki": {"anki_deck": "",
                                       "anki_field": ""}
                              }

        conf_file: dict[str, dict[str, Any]]
        if not os.path.exists(CONFIG_FILE_PATH):
            conf_file = {}  # type: ignore
        else:
            with open(CONFIG_FILE_PATH, "r", encoding="UTF-8") as f:
                conf_file = json.load(f)

        validate_json(checking_scheme=conf_file, default_scheme=standard_conf_file)
        lang_pack = loaded_plugins.get_language_package(conf_file["app"]["language_package"])

        if not conf_file["directories"]["media_dir"] or not os.path.isdir(conf_file["directories"]["media_dir"]):
            conf_file["directories"]["media_dir"] = askdirectory(title=lang_pack.choose_media_dir_message,
                                                                 mustexist=True,
                                                                 initialdir=MEDIA_DOWNLOADING_LOCATION)
            if not conf_file["directories"]["media_dir"]:
                return (conf_file, lang_pack, True)

        if not conf_file["directories"]["last_open_file"] or not os.path.isfile(
                conf_file["directories"]["last_open_file"]):
            conf_file["directories"]["last_open_file"] = askopenfilename(title=lang_pack.choose_deck_file_message,
                                                                         filetypes=(("JSON", ".json"),),
                                                                         initialdir="./")
            if not conf_file["directories"]["last_open_file"]:
                return (conf_file, lang_pack, True)

        if not conf_file["directories"]["last_save_dir"] or not os.path.isdir(
                conf_file["directories"]["last_save_dir"]):
            conf_file["directories"]["last_save_dir"] = askdirectory(title=lang_pack.choose_save_dir_message,
                                                                     mustexist=True,
                                                                     initialdir="./")
            if not conf_file["directories"]["last_save_dir"]:
                return (conf_file, lang_pack, True)

        return (conf_file, lang_pack, False)

    @staticmethod
    def load_history_file() -> dict:
        if not os.path.exists(HISTORY_FILE_PATH):
            history_json = {}
        else:
            with open(HISTORY_FILE_PATH, "r", encoding="UTF-8") as f:
                history_json = json.load(f)
        return history_json

    @property
    @error_handler(show_errors)
    def word(self):
        return self.word_text.get(1.0, "end").strip()

    @property
    @error_handler(show_errors)
    def definition(self):
        return self.definition_text.get(1.0, "end").rstrip()

    @error_handler(show_errors)
    def get_sentence(self, n: int):
        return self.sent_text_list[n].get(1.0, "end").rstrip()

    @error_handler(show_errors)
    def change_file(self):
        new_file_path = askopenfilename(title=self.lang_pack.choose_deck_file_message,
                                   filetypes=(("JSON", ".json"),),
                                   initialdir="./")
        if not new_file_path:
            return

        new_save_dir = askdirectory(title=self.lang_pack.choose_save_dir_message,
                                    initialdir="./")
        if not new_save_dir:
            return

        self.save_files()
        self.session_start = datetime.now()
        self.str_session_start = self.session_start.strftime("%d-%m-%Y-%H-%M-%S")
        self.configurations["directories"]["last_save_dir"] = new_save_dir
        self.configurations["directories"]["last_open_file"] = new_file_path
        if self.history.get(new_file_path) is None:
            self.history[new_file_path] = -1

        self.deck = Deck(deck_path=self.configurations["directories"]["last_open_file"],
                         current_deck_pointer=self.history[self.configurations["directories"]["last_open_file"]],
                         card_generator=self.cd)
        self.saved_cards_data = SavedDataDeck()
        self.refresh()

    @error_handler(show_errors)
    def create_file_dialog(self):
        @error_handler(self.show_errors)
        def create_file():
            def foo():
                skip_var.set(True)
                copy_encounter.destroy()

            new_file_name = remove_special_chars(name_entry.get().strip(), sep="_")
            if not new_file_name:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=self.lang_pack.create_file_no_file_name_was_given_message)
                return

            new_file_path = f"{new_file_dir}/{new_file_name}.json"
            skip_var = BooleanVar()
            skip_var.set(False)
            if os.path.exists(new_file_path):
                copy_encounter = self.Toplevel(create_file_win)
                copy_encounter.withdraw()
                message = self.lang_pack.create_file_file_already_exists_message
                encounter_label = self.Label(copy_encounter, text=message, relief="ridge")
                skip_encounter_button = self.Button(copy_encounter,
                                                    text=self.lang_pack.create_file_skip_encounter_button_text,
                                                    command=lambda: foo())
                rewrite_encounter_button = self.Button(copy_encounter,
                                                       text=self.lang_pack.create_file_rewrite_encounter_button_text,
                                                       command=lambda: copy_encounter.destroy())

                encounter_label.grid(row=0, column=0, padx=5, pady=5)
                skip_encounter_button.grid(row=1, column=0, padx=5, pady=5, sticky="news")
                rewrite_encounter_button.grid(row=2, column=0, padx=5, pady=5, sticky="news")
                copy_encounter.deiconify()
                spawn_toplevel_in_center(self, copy_encounter)
                create_file_win.wait_window(copy_encounter)

            create_file_win.destroy()

            if not skip_var.get():
                with open(new_file_path, "w", encoding="UTF-8") as new_file:
                    json.dump([], new_file)

            new_save_dir = askdirectory(title=self.lang_pack.choose_save_dir_message, initialdir="./")
            if not new_save_dir:
                return

            self.save_files()
            self.session_start = datetime.now()
            self.str_session_start = self.session_start.strftime("%d-%m-%Y-%H-%M-%S")
            self.configurations["directories"]["last_save_dir"] = new_save_dir
            self.configurations["directories"]["last_open_file"] = new_file_path
            if self.history.get(new_file_path) is None:
                self.history[new_file_path] = -1

            self.deck = Deck(deck_path=new_file_path,
                             current_deck_pointer=self.history[new_file_path],
                             card_generator=self.cd)
            self.saved_cards_data = SavedDataDeck()
            self.refresh()

        new_file_dir = askdirectory(title=self.lang_pack.create_file_choose_dir_message, initialdir="./")
        if not new_file_dir:
            return
        create_file_win = self.Toplevel()
        create_file_win.withdraw()
        name_entry = self.Entry(create_file_win,
                                placeholder=self.lang_pack.create_file_name_entry_placeholder,
                                justify="center")
        name_button = self.Button(create_file_win,
                                  text=self.lang_pack.create_file_name_button_placeholder,
                                  command=create_file)
        name_entry.grid(row=0, column=0, padx=5, pady=3, sticky="news")
        name_button.grid(row=1, column=0, padx=5, pady=3, sticky="ns")
        create_file_win.deiconify()
        spawn_toplevel_in_center(self, create_file_win)
        name_entry.focus()
        create_file_win.bind("<Escape>", lambda event: create_file_win.destroy())
        create_file_win.bind("<Return>", lambda event: create_file())

    @error_handler(show_errors)
    def save_files(self):
        self.configurations["app"]["main_window_geometry"] = self.geometry()
        self.configurations["tags_hierarchical_pref"] = self.tag_prefix_field.get().strip()
        self.save_conf_file()

        self.history[self.configurations["directories"]["last_open_file"]] = self.deck.get_pointer_position() - 1
        self.deck.save()
        with open(HISTORY_FILE_PATH, "w") as saving_f:
            json.dump(self.history, saving_f, indent=4)

        deck_name = os.path.basename(self.configurations["directories"]["last_open_file"]).split(sep=".")[0]
        saving_path = "{}/{}".format(self.configurations["directories"]["last_save_dir"], deck_name)
        self.deck_saver.save(self.saved_cards_data, CardStatus.ADD,
                             f"{saving_path}_{self.str_session_start}",
                             self.card_processor.get_card_image_name,
                             self.card_processor.get_card_audio_name)

        self.audio_saver.save(self.saved_cards_data, CardStatus.ADD,
                               f"{saving_path}_{self.str_session_start}_audios",
                               self.card_processor.get_card_image_name,
                               self.card_processor.get_card_audio_name)

        self.buried_saver.save(self.saved_cards_data, CardStatus.BURY,
                               f"{saving_path}_{self.str_session_start}_buried",
                               self.card_processor.get_card_image_name,
                               self.card_processor.get_card_audio_name)

    @error_handler(show_errors)
    def help_command(self):
        mes = self.lang_pack.buttons_hotkeys_help_message
        self.show_window(title=self.lang_pack.buttons_hotkeys_help_toplevel_title,
                         text=mes)

    @error_handler(show_errors)
    def get_query_language_help(self):
        standard_fields = f"""
{FIELDS.word}: {self.lang_pack.word_field_help}
{FIELDS.alt_terms}: {self.lang_pack.alt_terms_field_help}
{FIELDS.definition}: {self.lang_pack.definition_field_help}
{FIELDS.sentences}: {self.lang_pack.sentences_field_help}
{FIELDS.img_links}: {self.lang_pack.img_links_field_help}
{FIELDS.audio_links}: {self.lang_pack.audio_links_field_help}
{FIELDS.dict_tags}: {self.lang_pack.dict_tags_field_help}
"""
        current_scheme = self.cd.scheme_docs
        lang_docs = self.lang_pack.query_language_docs

        self.show_window(self.lang_pack.query_language_toplevel_title,
                         f"{self.lang_pack.general_scheme_label}:\n{standard_fields}\n"
                         f"{self.lang_pack.current_scheme_label}:\n{current_scheme}\n"
                         f"{self.lang_pack.query_language_label}:\n{lang_docs}")

    @error_handler(show_errors)
    def download_audio(self, choose_file=False, closing=False):
        if choose_file:
            self.save_files()
            audio_file_name = askopenfilename(title=self.lang_pack.download_audio_choose_audio_file_title,
                                              filetypes=(("JSON", ".json"),),
                                              initialdir="./")
            if not audio_file_name:
                return
            with open(audio_file_name, encoding="UTF-8") as audio_file:
                audio_links_list = json.load(audio_file)
        else:
            audio_links_list = self.saved_cards_data.get_audio_data(CardStatus.ADD)
        audio_downloader = AudioDownloader(master=self,
                                           headers=self.headers,
                                           timeout=1,
                                           request_delay=3_000,
                                           temp_dir="./temp/",
                                           saving_dir=self.configurations["directories"]["media_dir"],
                                           toplevel_cfg=self.theme.toplevel_cfg,
                                           pb_cfg={"length": self.winfo_width()},
                                           label_cfg=self.theme.label_cfg,
                                           button_cfg=self.theme.button_cfg,
                                           checkbutton_cfg=self.theme.checkbutton_cfg
                                           )
        if closing:
            audio_downloader.bind("<Destroy>", lambda event: self.destroy() if isinstance(event.widget, Toplevel) else None)
        spawn_toplevel_in_center(self, audio_downloader)
        audio_downloader.download_audio(audio_links_list)

    @error_handler(show_errors)
    def change_media_dir(self):
        media_dir =  askdirectory(title=self.lang_pack.choose_media_dir_message,
                                  mustexist=True,
                                  initialdir=MEDIA_DOWNLOADING_LOCATION)
        if media_dir:
            self.configurations["directories"]["media_dir"] = media_dir

    @error_handler(show_errors)
    def save_button(self):
        self.save_files()
        messagebox.showinfo(message=self.lang_pack.save_files_message)

    @error_handler(show_errors)
    def define_word(self, word_query: str, additional_query: str) -> bool:
        try:
            exact_pattern = re.compile(r"\b{}\b".format(word_query))
        except re.error:
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=self.lang_pack.define_word_wrong_regex_message)
            return True

        exact_word_filter = lambda comparable: re.search(exact_pattern, comparable)
        try:
            additional_filter = get_card_filter(additional_query) if additional_query else None
            if self.deck.add_card_to_deck(query=word_query,
                                          word_filter=exact_word_filter,
                                          additional_filter=additional_filter):
                self.refresh()
                return False
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=self.lang_pack.define_word_word_not_found_message)
        except ParsingException as e:
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=str(e))
        return True

    @error_handler(show_errors)
    def add_word_dialog(self):
        @error_handler(self.show_errors)
        def get_word():
            clean_word = add_word_entry.get().strip()
            additional_query = additional_filter_entry.get(1.0, "end").strip()
            if not self.define_word(clean_word, additional_query):
                add_word_frame.destroy()
            else:
                add_word_frame.withdraw()
                add_word_frame.deiconify()

        add_word_frame = self.Toplevel(self)
        add_word_frame.withdraw()

        add_word_frame.grid_columnconfigure(0, weight=1)
        add_word_frame.title(self.lang_pack.add_word_frame_title)

        add_word_entry = self.Entry(add_word_frame,
                                    placeholder=self.lang_pack.add_word_entry_placeholder)
        add_word_entry.focus()
        add_word_entry.grid(row=0, column=0, padx=5, pady=3, sticky="we")

        additional_filter_entry = self.Text(add_word_frame,
                                            placeholder=self.lang_pack.add_word_additional_filter_entry_placeholder,
                                            height=5)
        additional_filter_entry.grid(row=1, column=0, padx=5, pady=3, sticky="we")

        start_parsing_button = self.Button(add_word_frame,
                                           text=self.lang_pack.add_word_start_parsing_button_text,
                                           command=get_word)
        start_parsing_button.grid(row=2, column=0, padx=5, pady=3, sticky="ns")

        add_word_frame.bind("<Escape>", lambda event: add_word_frame.destroy())
        add_word_frame.bind("<Return>", lambda event: get_word())
        add_word_frame.deiconify()
        spawn_toplevel_in_center(master=self, toplevel_widget=add_word_frame,
                                 desired_toplevel_width=self.winfo_width())

    @error_handler(show_errors)
    def find_dialog(self):
        @error_handler(self.show_errors)
        def go_to():
            find_query = find_entry.get(1.0, "end").strip()
            if not find_query:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=self.lang_pack.find_dialog_empty_query_message)
                return

            if find_query.startswith("->"):
                if not (move_quotient := find_query[2:]).lstrip("-").isdigit():
                    messagebox.showerror(title=self.lang_pack.error_title,
                                         message=self.lang_pack.find_dialog_wrong_move_message)
                else:
                    self.replace_decks_pointers(int(move_quotient))
                find_frame.destroy()
                return

            try:
                searching_filter = get_card_filter(find_query)
            except ParsingException as e:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=str(e))
                find_frame.withdraw()
                find_frame.deiconify()
                return

            if (move_list := self.deck.find_card(searching_func=searching_filter)):
                def rotate(n: int):
                    nonlocal move_list, found_item_number

                    found_item_number += n
                    rotate_frame.title(f"{found_item_number}/{len(move_list) + 1}")

                    if n > 0:
                        current_offset = move_list.get_pointed_item()
                        move_list.move(n)
                    else:
                        move_list.move(n)
                        current_offset = -move_list.get_pointed_item()

                    left["state"] = "disabled" if not move_list.get_pointer_position() else "normal"
                    right["state"] = "disabled" if move_list.get_pointer_position() == len(move_list) else "normal"

                    self.replace_decks_pointers(current_offset)

                find_frame.destroy()

                found_item_number = 1
                rotate_frame = self.Toplevel(self)
                rotate_frame.title(f"{found_item_number}/{len(move_list) + 1}")

                left = self.Button(rotate_frame, text="<", command=lambda: rotate(-1))
                left["state"] = "disabled"
                left.grid(row=0, column=0)

                right = self.Button(rotate_frame, text=">", command=lambda: rotate(1))
                right.grid(row=0, column=2)

                done_button_text = self.Button(rotate_frame,
                                               text=self.lang_pack.find_dialog_done_button_text,
                                               command=lambda: rotate_frame.destroy())
                done_button_text.grid(row=0, column=1)
                spawn_toplevel_in_center(self, rotate_frame)
                rotate_frame.bind("<Escape>", lambda _: rotate_frame.destroy())
                return
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=self.lang_pack.find_dialog_nothing_found_message)
            find_frame.withdraw()
            find_frame.deiconify()

        find_frame = self.Toplevel(self)
        find_frame.withdraw()
        find_frame.title(self.lang_pack.find_dialog_find_frame_title)
        find_frame.grid_columnconfigure(0, weight=1)
        find_entry = self.Text(find_frame, height=5)
        find_entry.grid(row=0, column=0, padx=5, pady=3, sticky="we")
        find_entry.focus()

        find_button = self.Button(find_frame,
                                  text=self.lang_pack.find_dialog_find_button_text,
                                  command=go_to)
        find_button.grid(row=1, column=0, padx=5, pady=3, sticky="ns")
        find_frame.bind("<Return>", lambda _: go_to())
        find_frame.bind("<Escape>", lambda _: find_frame.destroy())
        find_frame.deiconify()
        spawn_toplevel_in_center(self, find_frame, desired_toplevel_width=self.winfo_width())

    @error_handler(show_errors)
    def statistics_dialog(self):
        statistics_window = self.Toplevel(self)
        statistics_window.withdraw()

        statistics_window.title(self.lang_pack.statistics_dialog_statistics_window_title)
        text_list = ((self.lang_pack.statistics_dialog_added_label,
                      self.lang_pack.statistics_dialog_buried_label,
                      self.lang_pack.statistics_dialog_skipped_label,
                      self.lang_pack.statistics_dialog_cards_left_label,
                      self.lang_pack.statistics_dialog_current_file_label,
                      self.lang_pack.statistics_dialog_saving_dir_label,
                      self.lang_pack.statistics_dialog_media_dir_label),
                     (self.saved_cards_data.get_card_status_stats(CardStatus.ADD),
                      self.saved_cards_data.get_card_status_stats(CardStatus.BURY),
                      self.saved_cards_data.get_card_status_stats(CardStatus.SKIP),
                      self.deck.get_n_cards_left(),
                      self.deck.deck_path,
                      self.configurations["directories"]["last_save_dir"],
                      self.configurations["directories"]["media_dir"]))

        scroll_frame = ScrolledFrame(statistics_window, scrollbars="horizontal")
        scroll_frame.pack()
        scroll_frame.bind_scroll_wheel(statistics_window)
        inner_frame = scroll_frame.display_widget(self.Frame)
        for row_index in range(len(text_list[0])):
            for column_index in range(2):
                info = self.Label(inner_frame, text=text_list[column_index][row_index], anchor="center",
                             relief="ridge")
                info.grid(column=column_index, row=row_index, sticky="news")

        statistics_window.bind("<Escape>", lambda _: statistics_window.destroy())
        statistics_window.update()
        current_frame_width = inner_frame.winfo_width()
        current_frame_height = inner_frame.winfo_height()
        scroll_frame.config(width=min(self.winfo_width(), current_frame_width),
                            height=min(self.winfo_height(), current_frame_height))
        spawn_toplevel_in_center(self, statistics_window)
        statistics_window.deiconify()

    @error_handler(show_errors)
    def anki_dialog(self):
        anki_toplevel = self.Toplevel(self)

        @error_handler(self.show_errors)
        def save_anki_settings_command():
            self.configurations["anki"]["anki_deck"] = anki_deck_entry.get().strip()
            self.configurations["anki"]["anki_field"] = anki_field_entry.get().strip()
            anki_toplevel.destroy()

        anki_toplevel.title(self.lang_pack.anki_dialog_anki_toplevel_title)
        anki_deck_entry = self.Entry(anki_toplevel,
                                     placeholder=self.lang_pack.anki_dialog_anki_deck_entry_placeholder)
        anki_deck_entry.insert(0, self.configurations["anki"]["anki_deck"])
        anki_deck_entry.fill_placeholder()

        anki_field_entry = self.Entry(anki_toplevel,
                                      placeholder=self.lang_pack.anki_dialog_anki_field_entry_placeholder)
        anki_field_entry.insert(0, self.configurations["anki"]["anki_field"])
        anki_field_entry.fill_placeholder()

        save_anki_settings_button = self.Button(anki_toplevel,
                                                text=self.lang_pack.anki_dialog_save_anki_settings_button_text,
                                                command=save_anki_settings_command)

        padx = pady = 5
        anki_deck_entry.grid(row=0, column=0, sticky="we", padx=padx, pady=pady)
        anki_field_entry.grid(row=1, column=0, sticky="we", padx=padx, pady=pady)
        save_anki_settings_button.grid(row=2, column=0, sticky="ns", padx=padx)
        anki_toplevel.bind("<Return>", lambda event: save_anki_settings_command())
        anki_toplevel.bind("<Escape>", lambda event: anki_toplevel.destroy())
        spawn_toplevel_in_center(self, anki_toplevel)

    @error_handler(show_errors)
    def change_theme(self):
        @error_handler(self.show_errors)
        def pick(name: str):
            self.configurations["app"]["theme"] = name
            messagebox.showinfo(message=self.lang_pack.restart_app_text)
            theme_toplevel.destroy()

        theme_toplevel = self.Toplevel(self)
        theme_toplevel.grid_columnconfigure(0, weight=1)
        for i, theme_name in enumerate(loaded_plugins.themes.loaded):
            b = self.Button(theme_toplevel, text=theme_name, command=lambda x=theme_name: pick(x))
            b.grid(row=i, column=0, sticky="we", padx=5, pady=5)
        theme_toplevel.bind("<Escape>", lambda event: theme_toplevel.destroy())
        spawn_toplevel_in_center(self, theme_toplevel)
    
    def change_language(self):
        @error_handler(self.show_errors)
        def pick(name: str):
            self.configurations["app"]["language_package"] = name
            messagebox.showinfo(message=self.lang_pack.restart_app_text)
            lang_pack_toplevel.destroy()

        lang_pack_toplevel = self.Toplevel(self)
        lang_pack_toplevel.grid_columnconfigure(0, weight=1)
        for i, lang_pack_name in enumerate(loaded_plugins.language_packages.loaded):
            b = self.Button(lang_pack_toplevel, text=lang_pack_name, command=lambda x=lang_pack_name: pick(x))
            b.grid(row=i, column=0, sticky="we", padx=5, pady=5)
        lang_pack_toplevel.bind("<Escape>", lambda event: lang_pack_toplevel.destroy())
        spawn_toplevel_in_center(self, lang_pack_toplevel)
    
    @error_handler(show_errors)
    def on_closing(self):
        if messagebox.askokcancel(title=self.lang_pack.on_closing_message_title,
                                  message=self.lang_pack.on_closing_message):
            self.save_files()
            self.gb.stop()
            self.download_audio(closing=True)
    
    @error_handler(show_errors)
    def web_search_command(self):
        search_term = self.word
        definition_search_query = search_term + " definition"
        webbrowser.open_new_tab(f"https://www.google.com/search?q={definition_search_query}")
        sentence_search_query = search_term + " sentence examples"
        webbrowser.open_new_tab(f"https://www.google.com/search?q={sentence_search_query}")
    
    @error_handler(show_errors)
    def configure_dictionary(self):
        WEB_PREF = "[web]"
        LOCAL_PREF = "[local]"
        DEFAULT_AUDIO_SRC = "default"

        @error_handler(self.show_errors)
        def pick_parser(typed_parser: str):
            if typed_parser.startswith(WEB_PREF):
                raw_name = typed_parser[len(WEB_PREF) + 1:]
                self.cd = loaded_plugins.get_web_card_generator(typed_parser[len(WEB_PREF) + 1:])
                self.configurations["scrappers"]["word_parser_type"] = "web"
            else:
                raw_name = typed_parser[len(LOCAL_PREF) + 1:]
                self.cd = loaded_plugins.get_local_card_generator(typed_parser[len(LOCAL_PREF) + 1:])
                self.configurations["scrappers"]["word_parser_type"] = "local"
            self.configurations["scrappers"]["word_parser_name"] = raw_name
            self.typed_word_parser_name = typed_parser
            self.deck.update_card_generator(self.cd)

        # dict
        dict_configuration_toplevel = self.Toplevel(self)
        dict_configuration_toplevel.grid_columnconfigure(1, weight=1)
        dict_configuration_toplevel.withdraw()

        dict_label = self.Label(dict_configuration_toplevel, text=self.lang_pack.configure_dictionary_dict_label_text)
        dict_label.grid(row=0, column=0, sticky="news")

        choose_wp_option = self.get_option_menu(
            dict_configuration_toplevel,
            init_text=self.typed_word_parser_name,
            values=[f"{WEB_PREF} {item}" for item in loaded_plugins.web_word_parsers.loaded] +
                   [f"{LOCAL_PREF} {item}" for item in loaded_plugins.local_word_parsers.loaded],
            command=lambda typed_parser: pick_parser(typed_parser))
        choose_wp_option.grid(row=0, column=1, sticky="news")

        # audio_getter
        audio_getter_label = self.Label(dict_configuration_toplevel,
                                        text=self.lang_pack.configure_dictionary_audio_getter_label_text)
        audio_getter_label.grid(row=1, column=0, sticky="news")

        @error_handler(self.show_errors)
        def pick_audio_getter(name: str):
            if name == DEFAULT_AUDIO_SRC:
                self.local_audio_getter = None
                self.configurations["scrappers"]["local_audio"] = ""
                self.sound_button["state"] = "normal" if self.dict_card_data.get(FIELDS.audio_links, []) else "disabled"
                return
            self.sound_button["state"] = "normal"
            self.configurations["scrappers"]["local_audio"] = name
            self.local_audio_getter = loaded_plugins.get_local_audio_getter(name)

        choose_audio_option = self.get_option_menu(
            dict_configuration_toplevel,
            init_text=DEFAULT_AUDIO_SRC if self.local_audio_getter is None else self.local_audio_getter.name,
            values=list(loaded_plugins.local_audio_getters.loaded) + [DEFAULT_AUDIO_SRC],
            command=lambda getter: pick_audio_getter(getter))
        choose_audio_option.grid(row=1, column=1, sticky="news")

        # card_processor
        card_processor_label = self.Label(dict_configuration_toplevel,
                                          text=self.lang_pack.configure_dictionary_card_processor_label_text)
        card_processor_label.grid(row=2, column=0, sticky="news")

        @error_handler(self.show_errors)
        def choose_card_processor(name: str):
            self.configurations["card_processor"] = name
            self.card_processor = loaded_plugins.get_card_processor(name)

        card_processor_option = self.get_option_menu(dict_configuration_toplevel,
                                                init_text=self.card_processor.name,
                                                values=loaded_plugins.card_processors.loaded,
                                                command=lambda processor: choose_card_processor(processor))
        card_processor_option.grid(row=2, column=1, sticky="news")

        format_processor_label = self.Label(dict_configuration_toplevel,
                                            text=self.lang_pack.configure_dictionary_format_processor_label_text)
        format_processor_label.grid(row=3, column=0, sticky="news")

        @error_handler(self.show_errors)
        def choose_format_processor(name: str):
            self.configurations["deck_saving_format"] = name
            self.deck_saver = loaded_plugins.get_deck_saving_formats(name)

        format_processor_option = self.get_option_menu(dict_configuration_toplevel,
                                                  init_text=self.deck_saver.name,
                                                  values=loaded_plugins.deck_saving_formats.loaded,
                                                  command=lambda format: choose_format_processor(format))
        format_processor_option.grid(row=3, column=1, sticky="news")

        dict_configuration_toplevel.bind("<Escape>", lambda event: dict_configuration_toplevel.destroy())
        dict_configuration_toplevel.bind("<Return>", lambda event: dict_configuration_toplevel.destroy())
        dict_configuration_toplevel.deiconify()
        spawn_toplevel_in_center(self, dict_configuration_toplevel)
    
    @error_handler(show_errors)
    def change_image_parser(self, given_image_parser_name: str):
        self.image_parser = loaded_plugins.get_image_parser(given_image_parser_name)
        self.configurations["scrappers"]["base_image_parser"] = given_image_parser_name
    
    @error_handler(show_errors)
    def change_sentence_parser(self, given_sentence_parser_name: str):
        self.sentence_parser = loaded_plugins.get_sentence_parser(given_sentence_parser_name)
        self.sentence_fetcher = SentenceFetcher(sent_fetcher=self.sentence_parser.get_sentence_batch,
                                                sentence_batch_size=self.sentence_batch_size)
        self.configurations["scrappers"]["base_sentence_parser"] = given_sentence_parser_name
    
    @error_handler(show_errors)
    def choose_sentence(self, sentence_number: int):
        word = self.word
        dict_tags = self.dict_card_data.get(FIELDS.dict_tags, {})
        self.dict_card_data[FIELDS.word] = word
        self.dict_card_data[FIELDS.definition] = self.definition

        picked_sentence = self.get_sentence(sentence_number)
        if not picked_sentence:
            picked_sentence = self.dict_card_data[FIELDS.word]
        self.dict_card_data[FIELDS.sentences] = [picked_sentence]

        additional = self.dict_card_data.get(SavedDataDeck.ADDITIONAL_DATA, {})
        user_tags = self.user_tags_field.get().strip()
        if user_tags:
            additional[SavedDataDeck.USER_TAGS] = user_tags

        if self.local_audio_getter is not None and (local_audios := self.local_audio_getter.get_local_audios(word, dict_tags)):
            additional[SavedDataDeck.AUDIO_DATA] = {}
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SRCS] = local_audios
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SRCS_TYPE] = SavedDataDeck.AUDIO_SRC_TYPE_LOCAL
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SAVING_PATHS] = [
                os.path.join(self.configurations["directories"]["media_dir"],
                             self.card_processor.get_save_audio_name(word,
                                                                     self.local_audio_getter.name,
                                                                     f"{i}",
                                                                     dict_tags))
                for i in range(len(local_audios))
            ]
        elif self.local_audio_getter is None and (web_audios := self.dict_card_data.get(FIELDS.audio_links, [])):
            additional[SavedDataDeck.AUDIO_DATA] = {}
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SRCS] = web_audios
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SRCS_TYPE] = SavedDataDeck.AUDIO_SRC_TYPE_WEB
            additional[SavedDataDeck.AUDIO_DATA][SavedDataDeck.AUDIO_SAVING_PATHS] = [
                os.path.join(self.configurations["directories"]["media_dir"],
                             self.card_processor.get_save_audio_name(word,
                                                                     self.typed_word_parser_name,
                                                                     f"{i}",
                                                                     dict_tags))
                for i in range(len(web_audios))
            ]

        if (hierarchical_prefix := self.tag_prefix_field.get().strip()):
            additional[SavedDataDeck.HIERARCHICAL_PREFIX] = hierarchical_prefix

        if additional:
            self.dict_card_data[SavedDataDeck.ADDITIONAL_DATA] = additional

        self.saved_cards_data.append(status=CardStatus.ADD, card_data=self.dict_card_data)
        if not self.deck.get_n_cards_left():
            self.deck.append(Card(self.dict_card_data))
        self.refresh()
    
    @error_handler(show_errors)
    def skip_command(self):
        if self.deck.get_n_cards_left():
            self.saved_cards_data.append(CardStatus.SKIP)
        self.refresh()

    @error_handler(show_errors)
    def replace_decks_pointers(self, n: int):
        self.saved_cards_data.move(min(n, self.deck.get_n_cards_left()))
        self.deck.move(n - 1)
        self.refresh()
    
    @error_handler(show_errors)
    def play_sound(self):
        @error_handler(self.show_errors)
        def sound_dialog(audio_src: list[str], info: list[str], play_command: Callable[[str, str], None]):
            assert len(audio_src) == len(info)

            playsound_toplevel = self.Toplevel(self)
            playsound_toplevel.withdraw()
            playsound_toplevel.title(self.lang_pack.play_sound_playsound_toplevel_title)
            playsound_toplevel.columnconfigure(0, weight=1)

            for i in range(len(audio_src)):
                playsound_toplevel.rowconfigure(i, weight=1)
                label = self.Text(playsound_toplevel, relief="ridge", height=3)
                label.insert(1.0, info[i])
                label["state"] = "disabled"
                label.grid(row=i, column=0)
                b = self.Button(playsound_toplevel,
                                text=self.lang_pack.sound_button_text,
                                command=lambda src=audio_src[i]: play_command(src, str(i)))
                b.grid(row=i, column=1, sticky="news")

            playsound_toplevel.bind("<Escape>", lambda _: playsound_toplevel.destroy())
            playsound_toplevel.deiconify()
            spawn_toplevel_in_center(self, playsound_toplevel,
                                     desired_toplevel_width=self.winfo_width()
                                     )

        @error_handler(self.show_errors)
        def show_download_error(exc):
            messagebox.showerror(message=f"{self.lang_pack.error_title}\n{exc}")

        @error_handler(self.show_errors)
        def web_playsound(src: str, postfix: str = ""):
            audio_name = self.card_processor.get_save_audio_name(word,
                                                                 self.typed_word_parser_name,
                                                                 "0",
                                                                 dict_tags)

            temp_audio_path = os.path.join(os.getcwd(), "temp", audio_name + postfix)
            success = True
            if not os.path.exists(temp_audio_path):
                success = AudioDownloader.fetch_audio(url=src,
                                                      save_path=temp_audio_path,
                                                      timeout=5,
                                                      headers=self.headers,
                                                      exception_action=lambda exc: show_download_error(exc))
            if success:
                playsound(temp_audio_path)

        @error_handler(self.show_errors)
        def local_playsound(src: str, postfix: str = ""):
            playsound(src)

        word = self.word
        dict_tags = self.dict_card_data.get(FIELDS.dict_tags, {})
        if self.local_audio_getter is not None:
            audio_file_paths = self.local_audio_getter.get_local_audios(word, dict_tags)
            if audio_file_paths:
                if len(audio_file_paths) == 1:
                    local_playsound(audio_file_paths[0])
                    return
                sound_dialog(audio_file_paths, audio_file_paths, local_playsound)
                return
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=self.lang_pack.play_sound_local_audio_not_found_message)
            return

        if (audio_file_urls := self.dict_card_data.get(FIELDS.audio_links)) is None or not audio_file_urls:
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=self.lang_pack.play_sound_no_audio_source_found_message)
            return

        elif len(audio_file_urls) == 1:
            web_playsound(audio_file_urls[0], "")
            return
        sound_dialog(audio_file_urls, audio_file_urls, web_playsound)
    
    @error_handler(show_errors)
    def open_anki_browser(self):
        @error_handler(self.show_errors)
        def invoke(action, **params):
            def request_anki(action, **params):
                return {'action': action, 'params': params, 'version': 6}
            import requests

            request_json = json.dumps(request_anki(action, **params)).encode('utf-8')
            try:
                res = requests.get("http://localhost:8765", data=request_json, timeout=1)
                res.raise_for_status()
            except requests.ConnectionError:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=self.lang_pack.request_anki_connection_error_message)
                return
            except requests.RequestException as e:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=f"{self.lang_pack.request_anki_general_request_error_message_prefix}: {e}")
                return

            response = res.json()
            if response['error'] is not None:
                messagebox.showerror(title=self.lang_pack.error_title,
                                     message=response['error'])
            return response['result']

        word = self.word_text.get(1.0, "end").strip()
        query_list = []
        if self.configurations["anki"]["anki_deck"]:
            query_list.append("deck:\"{}\"".format(self.configurations["anki"]["anki_deck"]))
        if self.configurations["anki"]["anki_field"]:
            query_list.append("\"{}:*{}*\"".format(self.configurations["anki"]["anki_field"],
                                                   word))
        else:
            query_list.append(f"*{word}*")
        result_query = " and ".join(query_list)
        invoke('guiBrowse', query=result_query)
    
    @error_handler(show_errors)
    def bury_command(self):
        self.saved_cards_data.append(status=CardStatus.BURY, card_data=self.dict_card_data)
        self.refresh()
    
    @error_handler(show_errors)
    def replace_sentences(self) -> None:
        sent_batch, error_message, local_flag = self.sentence_fetcher.get_sentence_batch(self.word)
        for text_field in self.sent_text_list:
            text_field.clear()
            text_field.fill_placeholder()
        for i in range(len(sent_batch)):
            self.sent_text_list[i].remove_placeholder()
            self.sent_text_list[i].insert(1.0, sent_batch[i])
        if error_message:
            messagebox.showerror(title=self.lang_pack.error_title,
                                 message=error_message)
        self.add_sentences_button["text"] = self.sentence_button_text if local_flag else self.sentence_button_text + " +"
    
    @error_handler(show_errors)
    def refresh(self) -> bool:
        @error_handler(self.show_errors)
        def fill_additional_dict_data(widget: Text, text: str):
            widget["state"] = "normal"
            widget.clear()
            widget.insert(1.0, text)
            widget["state"] = "disabled"

        self.dict_card_data = self.deck.get_card().to_dict()
        self.card_processor.process_card(self.dict_card_data)

        self.prev_button["state"] = "normal" if self.deck.get_pointer_position() != self.deck.get_starting_position() + 1 \
                                             else "disabled"

        self.title(f"{self.lang_pack.main_window_title_prefix}: {self.deck.get_n_cards_left()}")

        self.word_text.clear()
        self.word_text.insert(1.0, self.dict_card_data.get(FIELDS.word, ""))
        self.word_text.focus()

        fill_additional_dict_data(self.dict_tags_field, Card.get_str_dict_tags(self.dict_card_data))
        fill_additional_dict_data(self.alt_terms_field, " ".join(self.dict_card_data.get(FIELDS.alt_terms, [])))

        self.definition_text.clear()
        self.definition_text.insert(1.0, self.dict_card_data.get(FIELDS.definition, ""))
        self.definition_text.fill_placeholder()

        self.sentence_fetcher(self.word, self.dict_card_data.get(FIELDS.sentences, []))
        self.replace_sentences()
        if not self.dict_card_data:
            # normal
            self.find_image_button["text"] = self.lang_pack.find_image_button_normal_text
            if not self.configurations["scrappers"]["local_audio"]:
                self.sound_button["state"] = "disabled"
            return False

        if self.dict_card_data.get(FIELDS.img_links, []):
            self.find_image_button["text"] = self.lang_pack.find_image_button_normal_text + \
                                             self.lang_pack.find_image_button_image_link_encountered_postfix
        else:
            self.find_image_button["text"] = self.lang_pack.find_image_button_normal_text

        if self.configurations["scrappers"]["local_audio"] or self.dict_card_data.get(FIELDS.audio_links, []):
            self.sound_button["state"] = "normal"
        else:
            self.sound_button["state"] = "disabled"
        return True
    
    @error_handler(show_errors)
    def start_image_search(self):
        @error_handler(self.show_errors)
        def connect_images_to_card(instance: ImageSearch):
            nonlocal word

            additional = self.dict_card_data.get(SavedDataDeck.ADDITIONAL_DATA)
            if additional is not None and \
                    (paths := additional.get(self.saved_cards_data.SAVED_IMAGES_PATHS)) is not None:
                for path in paths:
                    if os.path.isfile(path):
                        os.remove(path)

            dict_tags = self.dict_card_data.get(FIELDS.dict_tags, {})

            names: list[str] = []
            for i in range(len(instance.working_state)):
                if instance.working_state[i]:
                    saving_name = "{}/{}"\
                        .format(self.configurations["directories"]["media_dir"],
                                self.card_processor
                                .get_save_image_name(word,
                                                     instance.images_source[i],
                                                     self.configurations["scrappers"]["base_image_parser"],
                                                     dict_tags))
                    instance.saving_images[i].save(saving_name)
                    names.append(saving_name)

            if names:
                if additional is None:
                    self.dict_card_data[SavedDataDeck.ADDITIONAL_DATA] = {}
                self.dict_card_data[SavedDataDeck.ADDITIONAL_DATA][self.saved_cards_data.SAVED_IMAGES_PATHS] = names

            x, y = instance.geometry().split(sep="+")[1:]
            self.configurations["app"]["image_search_position"] = f"+{x}+{y}"

        word = self.word
        show_image_width = 250
        button_pady = button_padx = 10
        height_lim = self.winfo_height() * 7 // 8
        image_finder = ImageSearch(master=self,
                                   main_params=self.theme.toplevel_cfg,
                                   search_term=word,
                                   saving_dir=self.configurations["directories"]["media_dir"],
                                   url_scrapper=self.image_parser.get_image_links,
                                   init_urls=self.dict_card_data
                                                 .get(FIELDS.img_links, []),
                                   local_images=self.dict_card_data
                                                    .get(SavedDataDeck.ADDITIONAL_DATA, {})
                                                    .get(self.saved_cards_data.SAVED_IMAGES_PATHS, []),
                                   headers=self.headers,
                                   on_close_action=connect_images_to_card,
                                   show_image_width=show_image_width,
                                   saving_image_width=300,
                                   button_padx=button_padx,
                                   button_pady=button_pady,
                                   window_height_limit=height_lim,
                                   on_closing_action=connect_images_to_card,
                                   command_button_params=self.theme.button_cfg,
                                   entry_params=self.theme.entry_cfg,
                                   frame_params=self.theme.frame_cfg
                                   )
        image_finder.focus()
        image_finder.grab_set()
        image_finder.geometry(self.configurations["app"]["image_search_position"])
        image_finder.start()


if __name__ == "__main__":
    root = App()
    root.mainloop()
