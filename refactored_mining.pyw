import importlib
import pkgutil
from tkinter import Label, Button, Checkbutton, Toplevel, Menu, Frame, BooleanVar, IntVar, Entry
from utils.widgets import TextWithPlaceholder as Text
from utils.widgets import EntryWithPlaceholder as Entry
from tkinter import messagebox

from tkinterdnd2 import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import Canvas
from tkinter import ttk

import parsers.image_parsers
import parsers.word_parsers.local
import parsers.word_parsers.web
import parsers.sentence_parsers

from CONSTS import *
from utils.cards import *
from utils.window_utils import get_option_menu


class App(Tk):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        self.CONFIG, error_code = App.load_conf_file()
        if error_code:
            self.destroy()
        self.save_conf_file()

        self.HISTORY = App.load_history_file()
        if not self.HISTORY.get(self.CONFIG["directories"]["last_open_file"]):
            self.HISTORY[self.CONFIG["directories"]["last_open_file"]] = 0
        self.web_word_parsers = App.get_web_word_parsers()
        self.local_word_parsers = App.get_local_word_parsers()
        self.web_sent_parsers = App.get_sentence_parsers()
        self.image_parsers = App.get_image_parsers()

        if self.CONFIG["scrappers"]["parser_type"] == "web":
            cd = CardGenerator(
                parsing_function=self.web_word_parsers[self.CONFIG["scrappers"]["parser_name"]].define,
                item_converter=self.web_word_parsers[self.CONFIG["scrappers"]["parser_name"]].translate)
        elif self.CONFIG["scrappers"]["parser_type"] == "local":
            cd = CardGenerator(
                local_dict_path="./media/{}.json".format(
                    self.web_word_parsers[self.CONFIG["scrappers"]["parser_name"]].DICTIONARY_PATH),
                item_converter=self.web_word_parsers[self.CONFIG["scrappers"]["parser_name"]].translate)
        else:
            raise NotImplemented("Unknown parser_type: {}!".format(self.CONFIG["scrappers"]["parser_type"]))

        self.deck = Deck(json_deck_path=self.CONFIG["directories"]["last_open_file"],
                         current_deck_pointer=self.HISTORY[self.CONFIG["directories"]["last_open_file"]],
                         card_generator=cd)

        main_menu = Menu(self)
        filemenu = Menu(main_menu, tearoff=0)
        filemenu.add_command(label="Создать", command=App.func_placeholder)
        filemenu.add_command(label="Открыть", command=App.func_placeholder)
        filemenu.add_command(label="Сохранить", command=App.func_placeholder)
        filemenu.add_separator()
        filemenu.add_command(label="Справка", command=App.func_placeholder)
        filemenu.add_separator()
        filemenu.add_command(label="Скачать аудио", command=App.func_placeholder)
        filemenu.add_separator()
        filemenu.add_command(label="Сменить пользователя", command=App.func_placeholder)
        main_menu.add_cascade(label="Файл", menu=filemenu)
        tag_menu = Menu(main_menu, tearoff=0)

        self.domain_var = BooleanVar(name="domain")
        self.level_var = BooleanVar(name="level")
        self.region_var = BooleanVar(name="region")
        self.usage_var = BooleanVar(name="usage")
        self.pos_var = BooleanVar(name="pos")

        tag_menu.add_checkbutton(label='domain', variable=self.domain_var)
        tag_menu.add_checkbutton(label='level', variable=self.level_var)
        tag_menu.add_checkbutton(label='region', variable=self.region_var)
        tag_menu.add_checkbutton(label='usage', variable=self.usage_var)
        tag_menu.add_checkbutton(label='pos', variable=self.pos_var)
        main_menu.add_cascade(label='Тэги', menu=tag_menu)

        main_menu.add_command(label="Добавить", command=App.func_placeholder)
        main_menu.add_command(label="Перейти", command=App.func_placeholder)
        main_menu.add_command(label="Статистика", command=App.func_placeholder)

        theme_menu = Menu(main_menu, tearoff=0)
        self.index2theme_map = {0: "white",
                                1: "dark"}
        self.theme2index_map = {value: key for key, value in self.index2theme_map.items()}

        self.theme_index_var = IntVar(value=self.theme2index_map[self.CONFIG["app"]["theme"]])
        theme_menu.add_radiobutton(label="Светлая", variable=self.theme_index_var, value=0, command=App.func_placeholder)
        theme_menu.add_radiobutton(label="Тёмная", variable=self.theme_index_var, value=1, command=App.func_placeholder)
        main_menu.add_cascade(label="Тема", menu=theme_menu)

        main_menu.add_command(label="Anki", command=App.func_placeholder)
        main_menu.add_command(label="Выход", command=App.func_placeholder)
        self.config(menu=main_menu)

        self.browse_button = Button(self, text="Найти в браузере", command=App.func_placeholder)
        self.config_word_parser_button = Button(self, text="Настроить словарь", command=App.func_placeholder)
        self.find_image_button = Button(self, text="Добавить изображение", command=App.func_placeholder)
        self.image_word_parsers_names = list(self.image_parsers)
        
        self.image_parser_name = self.CONFIG["scrappers"]["base_image_parser"]
        self.image_parser_option_menu = get_option_menu(self,
                                                        init_text=self.image_parser_name,
                                                        values=self.image_word_parsers_names,
                                                        command=App.func_placeholder,
                                                        widget_configuration={},
                                                        option_submenu_params={})

        self.add_sentences_button = Button(self, text="Добавить предложения")
        self.sentence_parser_name = self.CONFIG["scrappers"]["base_sentence_parser"]
        self.sentence_parser_option_menu = get_option_menu(self,
                                                           init_text=self.sentence_parser_name,
                                                           values=list(self.web_sent_parsers),
                                                           command=App.func_placeholder,
                                                           widget_configuration={},
                                                           option_submenu_params={})

        self.word_text = Text(self, placeholder="Слово", height=2)
        self.alt_terms_field = Text(self, relief="ridge", state="disabled", height=1)
        self.meaning_text = Text(self, placeholder="Значение")

        self.sent_text_list = []
        Buttons_list = []
        button_width = 3
        for i in range(5):
            self.sent_text_list.append(Text(self, placeholder=f"Предложение {i + 1}"))
            self.sent_text_list[-1].fill_placeholder()
            Buttons_list.append(Button(self, text=f"{i + 1}", command=App.func_placeholder, width=button_width))

        self.delete_button = Button(self, text="Del", command=lambda: App.func_placeholder, width=button_width)
        self.prev_button = Button(self, text="Prev", command=App.func_placeholder, state="disabled", width=button_width)
        self.sound_button = Button(self, text="Play", command=App.func_placeholder, width=button_width)
        self.anki_button = Button(self, text="Anki", command=App.func_placeholder, width=button_width)
        self.skip_button = Button(self, text="Skip", command=App.func_placeholder, width=button_width)

        self.user_tags_field = Entry(self, placeholder="Тэги")
        self.user_tags_field.fill_placeholder()

        self.tag_prefix_field = Entry(self, justify="center", width=8)
        self.tag_prefix_field.insert(0, self.CONFIG["tags"]["hierarchical_pref"])
        self.dict_tags_field = Text(self, relief="ridge", state="disabled", height=2)

        Text_padx = 10
        Text_pady = 2
        # Расстановка виджетов
        self.browse_button.grid(row=0, column=0, padx=(Text_padx, 0), pady=(Text_pady, 0), sticky="news", columnspan=4)
        self.config_word_parser_button.grid(row=0, column=4, padx=(0, Text_padx), pady=(Text_pady, 0),
                                            columnspan=4, sticky="news")

        self.word_text.grid(row=1, column=0, padx=Text_padx, pady=Text_pady, columnspan=8, sticky="news")

        self.alt_terms_field.grid(row=2, column=0, padx=Text_padx, columnspan=8, sticky="news")

        self.find_image_button.grid(row=3, column=0, padx=(Text_padx, 0), pady=Text_pady, sticky="news", columnspan=4)
        self.image_parser_option_menu.grid(row=3, column=4, padx=(0, Text_padx), pady=Text_pady, columnspan=4,
                                           sticky="news")

        self.meaning_text.grid(row=4, column=0, padx=Text_padx, columnspan=8, sticky="news")

        self.add_sentences_button.grid(row=5, column=0, padx=(Text_padx, 0), pady=Text_pady, sticky="news", columnspan=4)
        self.sentence_parser_option_menu.grid(row=5, column=4, padx=(0, Text_padx), pady=Text_pady, columnspan=4,
                                              sticky="news")

        for i in range(5):
            c_pady = Text_pady if i % 2 else 0
            self.sent_text_list[i].grid(row=6 + i, column=0, columnspan=6, padx=Text_padx, pady=c_pady, sticky="news")
            Buttons_list[i].grid(row=6 + i, column=6, padx=0, pady=c_pady, sticky="ns")

        self.delete_button.grid(row=6, column=7, padx=Text_padx, pady=0, sticky="ns")
        self.prev_button.grid(row=7, column=7, padx=Text_padx, pady=Text_pady, sticky="ns")
        self.sound_button.grid(row=8, column=7, padx=Text_padx, pady=0, sticky="ns")
        self.anki_button.grid(row=9, column=7, padx=Text_padx, pady=Text_pady, sticky="ns")
        self.skip_button.grid(row=10, column=7, padx=Text_padx, pady=0, sticky="ns")

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

        self.new_order = [self.browse_button, self.word_text, self.find_image_button, self.meaning_text,
                          self.add_sentences_button] + self.sent_text_list + \
                         [self.user_tags_field] + Buttons_list + [self.delete_button, self.prev_button,
                                                                       self.anki_button, self.skip_button,
                                                                       self.tag_prefix_field]

        for widget_index in range(len(self.new_order)):
            self.new_order[widget_index].lift()
            self.new_order[widget_index].bind("<Tab>", focus_next_window)
            self.new_order[widget_index].bind("<Shift-Tab>", focus_prev_window)

        self.minsize(500, 0)
        self.geometry(self.CONFIG["app"]["main_window_geometry"])
        self.configure()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    @staticmethod
    def func_placeholder():
        return 0

    @staticmethod
    def load_history_file() -> dict:
        if not os.path.exists(HISTORY_FILE_PATH):
            history_json = {}
        else:
            with open(HISTORY_FILE_PATH, "r", encoding="UTF-8") as f:
                history_json = json.load(f)
        return history_json

    def save_conf_file(self):
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(self.CONFIG, f, indent=3)

    @staticmethod
    def load_conf_file() -> (dict, bool):
        standard_conf_file = {"app": {"theme": "dark",
                                      "main_window_geometry": "500x800+0+0",
                                      "image_search_position": "+0+0"},
                              "scrappers": {"base_sentence_parser": "web_sentencedict",
                                            "parser_type": "web",
                                            "parser_name": "cambridge_US",
                                            "base_image_parser": "google",
                                            "local_search_type": 0,
                                            "local_audio": "",
                                            "non_pos_specific_search": False},
                              "directories": {"media_dir": "",
                                              "last_open_file": "",
                                              "last_save_dir": ""},
                              "tags": {"hierarchical_pref": "eng",
                                       "include_domain": True,
                                       "include_level": True,
                                       "include_region": True,
                                       "include_usage": True,
                                       "include_pos": True},
                              "anki": {"anki_deck": "",
                                       "anki_field": ""}
                              }

        if not os.path.exists(CONFIG_FILE_PATH):
            conf_file = {}
        else:
            with open(CONFIG_FILE_PATH, "r", encoding="UTF-8") as f:
                conf_file = json.load(f)

        check_queue = [(standard_conf_file, conf_file)]
        for (src, dst) in check_queue:
            for checking_key in src:
                if dst.get(checking_key) is None:
                    dst[checking_key] = src[checking_key]
                elif type(dst[checking_key]) == dict:
                    check_queue.append((src[checking_key], dst[checking_key]))

        if not conf_file["directories"]["media_dir"]:
            conf_file["directories"]["media_dir"] = askdirectory(title="Выберете директорию для медиа файлов",
                                                                 mustexist=True,
                                                                 initialdir=STANDARD_ANKI_MEDIA)
            if not conf_file["directories"]["media_dir"]:
                return conf_file, 1
                        
        if not conf_file["directories"]["last_open_file"]:
            conf_file["directories"]["last_open_file"] = askopenfilename(title="Выберете JSON файл со словами",
                                                                         filetypes=(("JSON", ".json"),),
                                                                         initialdir="./")
            if not conf_file["directories"]["media_dir"]:
                return conf_file, 1
            
        if not conf_file["directories"]["last_save_dir"]:
            conf_file["directories"]["last_save_dir"] = askdirectory(title="Выберете директорию сохранения",
                                                                     mustexist=True,
                                                                     initialdir="./")
            if not conf_file["directories"]["media_dir"]:
                return conf_file, 1
        return conf_file, 0

    @staticmethod
    def iter_namespace(ns_pkg):
        # Specifying the second argument (prefix) to iter_modules makes the
        # returned name an absolute name instead of a relative one. This allows
        # import_module to work without having to do additional modification to
        # the name.
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

    @staticmethod
    def get_web_word_parsers() -> dict:
        web_word_parsers = {}
        for finder, name, ispkg in App.iter_namespace(parsers.word_parsers.web):
            parser_trunc_name = name.split(sep=".")[-1]
            if name.startswith('parsers.word_parsers.web'):
                web_word_parsers[parser_trunc_name] = importlib.import_module(name)
        return web_word_parsers

    @staticmethod
    def get_local_word_parsers() -> dict:
        local_word_parsers = {}
        for finder, name, ispkg in App.iter_namespace(parsers.word_parsers.local):
            parser_trunc_name = name.split(sep=".")[-1]
            if name.startswith('parsers.word_parsers.local'):
                local_word_parsers[parser_trunc_name] = importlib.import_module(name)
        return local_word_parsers

    @staticmethod
    def get_sentence_parsers() -> dict:
        web_sent_parsers = {}
        for finder, name, ispkg in App.iter_namespace(parsers.sentence_parsers):
            parser_trunc_name = name.split(sep=".")[-1]
            if name.startswith('parsers.sentence_parsers.web'):
                web_sent_parsers[parser_trunc_name] = importlib.import_module(name)
        return web_sent_parsers

    @staticmethod
    def get_image_parsers() -> dict:
        image_parsers = {}
        for finder, name, ispkg in App.iter_namespace(parsers.image_parsers):
            parser_trunc_name = name.split(sep=".")[-1]
            image_parsers[parser_trunc_name] = importlib.import_module(name)
        return image_parsers

    def save_files(self):
        """
        Сохраняет файлы если они не пустые или есть изменения
        """
        # получение координат на экране через self.winfo_rootx(), self.winfo_rooty() даёт некоторое смещение
        self.CONFIG["app"]["main_window_geometry"] = self.winfo_geometry()
        self.CONFIG["tags"]["hierarchical_pref"] = self.tag_prefix_field.get()
        self.CONFIG["tags"]["include_domain"] = self.domain_var.get()
        self.CONFIG["tags"]["include_level"] = self.level_var.get()
        self.CONFIG["tags"]["include_region"] = self.region_var.get()
        self.CONFIG["tags"]["include_usage"] = self.usage_var.get()
        self.CONFIG["tags"]["include_pos"] = self.pos_var.get()
        self.save_conf_file()

        self.HISTORY[self.CONFIG["directories"]["last_open_file"]] = self.deck.get_deck_pointer()

        with open(self.CONFIG["directories"]["last_open_file"], "w", encoding="utf-8") as new_write_file:
            json.dump(self.deck.get_deck(), new_write_file, indent=4)

        # self.save_audio_file()

        with open(HISTORY_FILE_PATH, "w") as saving_f:
            json.dump(self.HISTORY, saving_f, indent=4)

        # if self.SKIPPED_FILE:
        #     self.save_skip_file()
    
    def on_closing(self):
        """
        Закрытие программы
        """
        if messagebox.askokcancel("Выход", "Вы точно хотите выйти?"):
            self.save_files()
            # self.bg.stop()
            # if self.AUDIO_INFO:
            #     self.download_audio(closing=True)
            # else:
            #     self.destroy()
            self.destroy()


if __name__ == "__main__":
    root = App()
    root.mainloop()
