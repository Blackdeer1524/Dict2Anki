import os
import shutil
from enum import IntEnum
from tkinter import Button, Checkbutton, Label, Toplevel, BooleanVar
from tkinter import messagebox
from tkinter import ttk

import requests

from utils.cards import SavedDataDeck
from utils.storages import FrozenDict
from utils.window_utils import spawn_toplevel_in_center


class AudioDownloader(Toplevel):
    class CopyEncounterAction(IntEnum):
        UNSPECIFIED = 0
        SKIP = 1
        REWRITE = 2

    def __init__(self, master, headers, timeout, request_delay=5_000,
                 temp_dir="./", saving_dir="./", local_media_dir="./",
                 toplevel_cfg=None, pb_cfg=None, label_cfg=None, button_cfg=None, checkbutton_cfg=None):
        self.toplevel_cfg = toplevel_cfg
        if self.toplevel_cfg is None:
            self.toplevel_cfg = {}
        if pb_cfg is None:
            pb_cfg = {}
        pb_cfg.pop("orient", None)
        pb_cfg.pop("mode", None)
        self.label_cfg = label_cfg
        if self.label_cfg is None:
            self.label_cfg = {}
        self.button_cfg = button_cfg
        if self.button_cfg is None:
            self.button_cfg = {}
        self.checkbutton_cfg = checkbutton_cfg
        if self.checkbutton_cfg is None:
            self.checkbutton_cfg = {}

        self.if_copy_encountered = AudioDownloader.CopyEncounterAction.UNSPECIFIED
        self.already_processed_audios = set()
        self.temp_dir = temp_dir
        self.saving_dir = saving_dir
        self.local_media_dir = local_media_dir
        self.headers = headers
        self.timeout = timeout
        self.request_delay = request_delay
        self.errors = {"error_types": {}, "missing_audios": []}

        super(AudioDownloader, self).__init__(master, **self.toplevel_cfg)
        self.withdraw()
        self.title("Скачивание аудио...")

        self.pb = ttk.Progressbar(self,
                                  orient='horizontal',
                                  mode='determinate',
                                  **pb_cfg)  # lenght = self.WIDTH - 2 * self.text_padx
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.pb.grid(column=0, row=0, padx=5, pady=5, sticky="news")
        self.current_word_label = Label(self, **self.label_cfg)
        self.current_word_label.grid(column=0, row=1, sticky="news")
        self.label_cfg.pop("relief", None)
        self.deiconify()
        spawn_toplevel_in_center(master, self)

    def catch_fetching_error(self, exception):
        exception_type = str(exception)
        if self.errors["error_types"].get(exception_type) is None:
            self.errors["error_types"][exception_type] = 1
        else:
            self.errors["error_types"][exception_type] += 1
        self.errors["missing_audios"].append(self.current_word_label["text"])

    @staticmethod
    def fetch_audio(url, save_path, headers, timeout=5, exception_action=lambda exc: None) -> bool:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            exception_action(e)
            return False
        audio_bin = r.content
        with open(save_path, "wb") as audio_file:
            audio_file.write(audio_bin)
        return True

    def download_audio(self, audio_links_list: list[FrozenDict]):
        item_gen = [(item[SavedDataDeck.AUDIO_SRCS_TYPE], src, dst)
                     for item in audio_links_list
                     for src, dst in zip(item[SavedDataDeck.AUDIO_SRCS], item[SavedDataDeck.AUDIO_SAVING_PATHS])]
        length = len(item_gen)

        def iterate(src_type: str, src: str, dst: str, index: int = 1):
            """
            :param index:
            :param word:
            :param pos:
            :param wp_name:
            :param url:
            :return:
            """
            def write_to_dst(_src_type: str, _src: str, _dst: str) -> bool:
                wait_flag = False
                if _src_type == SavedDataDeck.AUDIO_SRC_TYPE_WEB:
                    wait_flag = self.fetch_audio(_src, _dst, self.headers, self.timeout,
                                                 self.catch_fetching_error)

                elif _src_type == SavedDataDeck.AUDIO_SRC_TYPE_LOCAL:
                    shutil.copy(src, _dst)
                return wait_flag

            self.pb["value"] = min(100.0, round(index / length * 100, 2))
            self.current_word_label["text"] = dst
            self.update()

            temp_audio_path = os.path.join(self.temp_dir, os.path.split(dst)[-1])

            wait_before_next_batch = False
            if dst not in self.already_processed_audios:
                self.already_processed_audios.add(dst)
                if not os.path.exists(dst) or self.if_copy_encountered == AudioDownloader.CopyEncounterAction.REWRITE:
                    if os.path.exists(temp_audio_path):
                        os.rename(temp_audio_path, dst)
                        wait_before_next_batch = False
                    else:
                        wait_before_next_batch = write_to_dst(src_type, src, dst)

                elif self.if_copy_encountered == AudioDownloader.CopyEncounterAction.SKIP:
                    wait_before_next_batch = False
                else:
                    def skip_encounter():
                        nonlocal wait_before_next_batch
                        if apply_to_all_var.get():
                            self.if_copy_encountered = AudioDownloader.CopyEncounterAction.SKIP
                        wait_before_next_batch = False
                        copy_encounter_tl.destroy()
                        self.grab_set()

                    def rewrite_encounter():
                        nonlocal wait_before_next_batch
                        if apply_to_all_var.get():
                            self.if_copy_encountered = AudioDownloader.CopyEncounterAction.REWRITE
                        copy_encounter_tl.destroy()
                        self.grab_set()
                        wait_before_next_batch = write_to_dst(src_type, src, dst)

                    apply_to_all_var = BooleanVar()

                    copy_encounter_tl = Toplevel(self, **self.toplevel_cfg)
                    copy_encounter_tl.withdraw()

                    message = f"Файл\n  {dst}  \nуже существует.\nВыберите нужную опцию:"

                    encounter_label = Label(copy_encounter_tl, text=message, relief="ridge",
                                            wraplength=self.winfo_width() * 2 // 3, **self.label_cfg)

                    skip_encounter_button = Button(copy_encounter_tl, text="Пропустить",
                                                   command=skip_encounter, **self.button_cfg)
                    rewrite_encounter_button = Button(copy_encounter_tl, text="Заменить",
                                                      command=rewrite_encounter, **self.button_cfg)
                    apply_to_all_button = Checkbutton(copy_encounter_tl, variable=apply_to_all_var,
                                                      text="Применить ко всем", **self.checkbutton_cfg)

                    encounter_label.grid(row=0, column=0, padx=5, pady=5, sticky="news")
                    skip_encounter_button.grid(row=1, column=0, padx=5, pady=5, sticky="news")
                    rewrite_encounter_button.grid(row=2, column=0, padx=5, pady=5, sticky="news")
                    apply_to_all_button.grid(row=3, column=0, padx=5, pady=5, sticky="news")

                    copy_encounter_tl.deiconify()
                    spawn_toplevel_in_center(self, copy_encounter_tl)

                    copy_encounter_tl.bind("<Escape>", lambda event: copy_encounter_tl.destroy())
                    self.wait_window(copy_encounter_tl)
                    self.grab_set()
            else:
                wait_before_next_batch = False

            if item_gen:
                delay = self.request_delay if wait_before_next_batch else 0
                src_type, src, dst = item_gen.pop(0)
                self.master.after(delay, lambda: iterate(src_type, src, dst, index + 1))
                return

            if self.errors["missing_audios"]:
                absent_audio_words = ", ".join(self.errors['missing_audios'])
                n_errors = f"Количество необработаных слов: {len(self.errors['missing_audios'])}\n"
                for error_type in self.errors["error_types"]:
                    n_errors += f"{error_type}: {self.errors['error_types'][error_type]}\n"

                error_message = f"{n_errors}\n\n{absent_audio_words}"
                messagebox.showerror(message=error_message)
            self.destroy()

        if item_gen:
            src_type, src, dst = item_gen.pop(0)
            iterate(src_type, src, dst, 1)
        else:
            self.destroy()
