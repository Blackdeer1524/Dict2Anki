import copy
import os
import time
from collections import UserList
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from functools import partial
from io import BytesIO
from tkinter import Entry, Button
from tkinter import Frame
from tkinter import Toplevel
from tkinter import messagebox
from typing import Callable, Generator, Any

import requests
from PIL import Image, ImageTk
from requests.exceptions import RequestException, ConnectTimeout
from tkinterdnd2 import DND_FILES, DND_TEXT

from consts.paths import SYSTEM
from utils.widgets import ScrolledFrame

if SYSTEM == "Linux":
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
else:
    from PIL import ImageGrab



class _UrlDeque(UserList):
    def __init__(self, data=None):
        """
        :param collection: iterable
        """
        super(_UrlDeque, self).__init__(data)

    def pop(self, n=1) -> list:
        return [self.data.pop() for _ in range(min(n, len(self.data)))]

    def popleft(self, n=1) -> list:
        return [self.data.pop(0) for _ in range(min(n, len(self.data)))]

    def appendleft(self, item):
        self.data.insert(0, item)

    def extendleft(self, collection):
        for i in range(len(collection) - 1, -1, -1):
            self.appendleft(collection[i])


class ImageSearch(Toplevel):
    class StatusCodes(IntEnum):
        NORMAL = 0
        RETRIABLE_FETCHING_ERROR = 1
        NON_RETRIABLE_FETCHING_ERROR = 2
        IMAGE_PROCESSING_ERROR = 3

    def __init__(self, master, search_term, **kwargs):
        """
        master: \n
        main_params: toplevel config
        frame_params: Frame config
        search_term: \n
        self.__url_scrapper: function that returns image urls by given query\n
        max_request_tries: how many retries allowed per one image-showing cycle\n
        init_urls: custom urls to be displayed\n
        init_images: custom images to be displayed\n
        headers: request headers\n
        timeout: request timeout\n
        show_image_width: maximum image display width\n
        show_image_height: maximum image display height\n
        saving_image_width: maximum image saving width\n
        saving_image_height: maximum image saving height\n
        n_images_in_row: \n
        n_rows: \n
        button_padx: \n
        button_pady: \n
        window_width_limit: maximum width of the window\n
        window_height_limit: maximum height of the window\n
        entry_params(**kwargs)s: entry widget params\n
        command_button_params(**kwargs): "Show more" and "Download" buttons params\n
        on_close_action(**kwargs): additional action performed on closing.
        """
        self.search_term: str = search_term
        self._img_urls: _UrlDeque = _UrlDeque(kwargs.get("init_urls", []))
        self._init_local_img_paths: list[str] = [image_path for image_path in kwargs.get("local_images", []) if
                                                 os.path.isfile(image_path)]
        self._init_images = kwargs.get("init_images", [])
        self._url_scrapper: Callable[[Any], Generator[tuple[list[str], str], int, tuple[list[str], str]]] = \
            kwargs.get("url_scrapper")

        self._image_url_gen = self._url_scrapper(search_term) if self._url_scrapper is not None else None
        self._scrapper_stop_flag = False

        self._button_bg = self.activebackground = "#FFFFFF"
        self._choose_color = "#FF0000"
        self._command_button_params = kwargs.get("command_button_params", {})
        self._entry_params = kwargs.get("entry_params", {})
        self._button_padx = kwargs.get("button_padx", 10)
        self._button_pady = kwargs.get("button_pady", 10)
        Toplevel.__init__(self, master, **kwargs.get("main_params", {}))

        self._headers = kwargs.get("headers")
        self._timeout = kwargs.get("timeout", 1)
        self._max_request_tries = kwargs.get("max_request_tries", 5)

        self._n_images_in_row = kwargs.get("n_images_in_row", 3)
        self._n_rows = kwargs.get("n_rows", 2)
        self._n_images_per_cycle = self._n_rows * self._n_images_in_row

        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self._n_images_per_cycle)

        self.saving_images: list[Image] = []
        self.images_source: list[str] = []
        self.working_state: list[bool] = []  # indices of picked buttons
        self.button_list: list[Button] = []

        self.optimal_visual_width = kwargs.get("show_image_width")
        self.optimal_visual_height = kwargs.get("show_image_height")
        self.optimal_result_width = kwargs.get("saving_image_width")
        self.optimal_result_height = kwargs.get("saving_image_height")

        self.title("Image search")
        self._search_field = Entry(self, justify="center", **self._entry_params)
        self._search_field.insert(0, self.search_term)
        self._start_search_button = Button(self, text="Search", command=self._restart_search,
                                            **self._command_button_params)

        self._search_field.grid(row=0, column=0, sticky="news",
                                 padx=(self._button_padx, 0), pady=self._button_pady)
        self._start_search_button.grid(row=0, column=1, sticky="news",
                                        padx=(0, self._button_padx), pady=self._button_pady)
        self._start_search_button["state"] = "normal" if self._url_scrapper else "disabled"

        self._sf = ScrolledFrame(self, scrollbars="both")
        self._sf.grid(row=1, column=0, columnspan=2)
        self._sf.bind_scroll_wheel(self)
        self._frame_params = kwargs.get("frame_params", {})
        self._inner_frame = self._sf.display_widget(partial(Frame, **self._frame_params))

        window_width_limit = kwargs.get("window_width_limit")
        window_height_limit = kwargs.get("window_height_limit")
        self.window_width_limit = window_width_limit if window_width_limit is not None else \
            master.winfo_screenwidth() * 6 // 7
        self.window_height_limit = window_height_limit if window_height_limit is not None else \
            master.winfo_screenheight() * 2 // 3

        self._show_more_gen = self._show_more()
        self._show_more_button = Button(master=self, text="Show more",
                                         command=lambda x=self._show_more_gen: next(x), **self._command_button_params)
        self._save_button = Button(master=self, text="Save",
                                    command=lambda: self.destroy(), **self._command_button_params)
        self._show_more_button.grid(row=3, column=0, sticky="news")
        self._save_button.grid(row=3, column=1, sticky="news")

        self._on_closing_action = kwargs.get("on_closing_action")

        self._cb = None
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", lambda event: self.destroy())
        self.bind("<Control-v>", lambda event: self._paste_image())
        self.drop_target_register(DND_FILES, DND_TEXT)
        self.dnd_bind('<<Drop>>', self._drop)

        self._command_widget_total_height = self._save_button.winfo_height() + self._search_field.winfo_height() + \
                                           2 * self._button_pady

    def _start_url_generator(self) -> None:
        if self._image_url_gen is None:
            self._scrapper_stop_flag = False
            return
        try:
            next(self._image_url_gen)
        except StopIteration as exception:
            messagebox.showerror(message=exception.value[1])
            self._scrapper_stop_flag = True

    def _generate_urls(self, batch_size):
        if self._image_url_gen is not None and not self._scrapper_stop_flag:
            try:
                url_batch, error_message = self._image_url_gen.send(batch_size)
            except StopIteration as exception:
                url_batch, error_message = exception.value
                self._scrapper_stop_flag = True
            self._img_urls.extend(url_batch)
            if error_message:
                messagebox.showerror(error_message)

    def start(self):
        if SYSTEM == "Linux":
            self._cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        for image_path in self._init_local_img_paths:
            self._process_single_image(Image.open(image_path), image_path)

        for index, custom_image in enumerate(self._init_images):
            self._process_single_image(custom_image, f"init-image-{index}")
            self.working_state[-1] = True
            self.button_list[-1]["bg"] = self._choose_color

        self._start_url_generator()
        if not self._scrapper_stop_flag:
            next(self._show_more_gen)
        self._resize_window()

    def _restart_search(self):
        self.search_term = self._search_field.get()
        if not self.search_term:
            messagebox.showerror(message="Empty search query")
            return

        self._scrapper_stop_flag = False
        self._image_url_gen = self._url_scrapper(self.search_term) if self._url_scrapper is not None else None
        self._start_url_generator()
        self._inner_frame = self._sf.display_widget(partial(Frame, **self._frame_params))
        self._img_urls.clear()

        left_indent = 0
        for i in range(len(self.working_state)):
            if self.working_state[i]:
                self.images_source[left_indent] = self.images_source[i]
                self.working_state[left_indent] = True
                self.saving_images[left_indent] = copy.deepcopy(self.saving_images[i])

                self.button_list[left_indent].grid_remove()
                b = Button(master=self._inner_frame,
                           image=self.button_list[i].image,
                           bg=self._choose_color,
                           activebackground=self.activebackground,
                           command=lambda button_index=left_indent:
                           self._choose_picture(button_index))
                b.image = self.button_list[i].image
                b.grid(row=left_indent // self._n_images_in_row,
                       column=left_indent % self._n_images_in_row,
                       padx=self._button_padx, pady=self._button_pady, sticky="news")
                self.button_list[left_indent] = b
                left_indent += 1

        del self.images_source[left_indent:]
        del self.button_list[left_indent:]
        del self.working_state[left_indent:]
        del self.saving_images[left_indent:]

        self._show_more_gen = self._show_more()
        self._show_more_button.configure(command=lambda x=self._show_more_gen: next(x))
        next(self._show_more_gen)

    def destroy(self):
        if self._on_closing_action is not None:
            self._on_closing_action(self)
        super(ImageSearch, self).destroy()

    def _resize_window(self):
        current_frame_width = self._inner_frame.winfo_width()
        current_frame_height = self._inner_frame.winfo_height()
        self._sf.config(width=min(self.window_width_limit, current_frame_width),
                        height=min(self.window_height_limit - self._command_widget_total_height,
                                     current_frame_height))

    @staticmethod
    def preprocess_image(img: Image, width: int = None, height: int = None) -> Image:
        processed_img = copy.copy(img)
        if width is not None and processed_img.width > width:
            k_width = width / processed_img.width
            processed_img = processed_img.resize((width, int(processed_img.height * k_width)),
                                                 Image.ANTIALIAS)

        if height is not None and processed_img.height > height:
            k_height = height / processed_img.height
            processed_img = processed_img.resize((int(processed_img.width * k_height), height),
                                                 Image.ANTIALIAS)
        return processed_img

    def fetch_image(self, url):
        """
        fetches image from web
        :param url: image url
        :return: status, button_img, img
        """
        try:
            response = requests.get(url, headers=self._headers, timeout=self._timeout)
            response.raise_for_status()
            content = response.content
            return ImageSearch.StatusCodes.NORMAL, content, url
        except ConnectTimeout:
            return ImageSearch.StatusCodes.RETRIABLE_FETCHING_ERROR, None, None
        except RequestException:
            return ImageSearch.StatusCodes.NON_RETRIABLE_FETCHING_ERROR, None, None

    def _schedule_batch_fetching(self, url_batch: list[str]):
        image_fetch_tasks = []
        for url in url_batch:
            image_fetch_tasks.append(self._pool.submit(self.fetch_image, url))
        return image_fetch_tasks

    def process_bin_data(self, content=None):
        try:
            img = Image.open(BytesIO(content))
            button_img = ImageTk.PhotoImage(
                self.preprocess_image(img, width=self.optimal_visual_width, height=self.optimal_visual_height))
            return ImageSearch.StatusCodes.NORMAL, button_img, img
        except (IOError, UnicodeError):
            return ImageSearch.StatusCodes.IMAGE_PROCESSING_ERROR, None, None

    def _choose_picture(self, button_index):
        self.working_state[button_index] = not self.working_state[button_index]
        self.button_list[button_index]["bg"] = self._choose_color if self.working_state[button_index] else self._button_bg

    def _place_buttons(self, button_image_batch):
        for j in range(len(button_image_batch)):
            b = Button(master=self._inner_frame, image=button_image_batch[j],
                       bg=self._button_bg, activebackground=self.activebackground,
                       command=lambda button_index=len(self.working_state): self._choose_picture(button_index))
            b.image = button_image_batch[j]
            b.grid(row=len(self.working_state) // self._n_images_in_row,
                   column=len(self.working_state) % self._n_images_in_row,
                   padx=self._button_padx, pady=self._button_pady, sticky="news")
            self.working_state.append(False)
            self.button_list.append(b)

        self._inner_frame.update()
        self._resize_window()

    def _process_batch(self, batch_size, n_retries=0):
        """
        :param batch_size: how many images to place
        :param n_retries: (if some error occurred) replace "bad" image with the new one and tries to fetch it.
        :return:
        """
        def add_fetching_to_queue():
            nonlocal n_retries
            self._generate_urls(1)
            if len(self._img_urls) and n_retries < self._max_request_tries:
                image_fetching_futures.append(self._pool.submit(self.fetch_image, self._img_urls.popleft()[0]))
                n_retries += 1

        self._generate_urls(batch_size)
        url_batch = self._img_urls.popleft(batch_size)
        button_images_batch = []
        image_fetching_futures = self._schedule_batch_fetching(url_batch)
        while image_fetching_futures:
            fetching_status, content, url = image_fetching_futures.pop(0).result()
            if fetching_status == ImageSearch.StatusCodes.NORMAL:
                processing_status, button_img, img = self.process_bin_data(content)
                if processing_status == ImageSearch.StatusCodes.NORMAL:
                    button_images_batch.append(button_img)
                    self.saving_images.append(img)
                    self.images_source.append(url)
                else:
                    add_fetching_to_queue()
            elif fetching_status == ImageSearch.StatusCodes.RETRIABLE_FETCHING_ERROR:
                self._img_urls.append(url)
                add_fetching_to_queue()
            else:
                add_fetching_to_queue()
        self._place_buttons(button_images_batch)

    def _show_more(self):
        self.update()
        self._show_more_button["state"] = "normal"
        while True:
            self._process_batch(self._n_images_per_cycle - len(self.working_state) % self._n_images_in_row)
            if self._scrapper_stop_flag and not len(self._img_urls):
                break
            yield
        self._show_more_button["state"] = "disabled"
        yield

    def _process_single_image(self, img: Image.Image, img_src: str):
        button_img_batch = [ImageTk.PhotoImage(
            self.preprocess_image(img, width=self.optimal_visual_width, height=self.optimal_visual_height))]
        
        self.saving_images.append(img)
        self.images_source.append(img_src)
        self._place_buttons(button_img_batch)

    def _drop(self, event):
        if event.data:
            data_path = event.data
            if os.path.exists(data_path):
                img = Image.open(data_path)
                self._process_single_image(img, data_path)
            elif data_path.startswith("http"):
                self._img_urls.appendleft(data_path)
                self._process_batch(batch_size=1, n_retries=self._max_request_tries)
        return event.action

    def _paste_image(self):
        img_src = f"clipboard-{time.time()}"
        if SYSTEM == "Linux":
            def pixbuf2image(pix):
                """Convert gdkpixbuf to PIL image"""
                data = pix.get_pixels()
                w = pix.props.width
                h = pix.props.height
                stride = pix.props.rowstride
                mode = "RGB"
                if pix.props.has_alpha == True:
                    mode = "RGBA"
                im = Image.frombytes(mode, (w, h), data, "raw", mode, stride)
                return im

            if self._cb.wait_is_image_available():
                pixbuf = self._cb.wait_for_image()
                self._process_single_image(pixbuf2image(pixbuf), img_src=img_src)
        else:
            self._process_single_image(ImageGrab.grabclipboard(), img_src=img_src)


if __name__ == "__main__":
    from tkinterdnd2 import Tk
    from parsers.image_parsers.google import get_image_links
    from pprint import pprint

    def start_image_search(word, master, **kwargs):
        image_finder = ImageSearch(search_term=word, master=master, **kwargs)
        image_finder.start()

    test_urls = ["https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"]

    # def get_image_links(search_term: None) -> list:
    #     return ["https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"]

    root = Tk()
    # root.withdraw()

    def save_on_closing(instance: ImageSearch):
        for i in range(len(instance.working_state)):
            if instance.working_state[i]:
                instance.saving_images[i].save(f"./{i}.png")
    
    def get_chosen_urls(instance: ImageSearch):
        res = []
        for i in range(len(instance.working_state)):
            if instance.working_state[i]:
                res.append(instance.saved_urls[i])
        assert len(res) == sum(instance.working_state)
        pprint(res)


    root.after(0, start_image_search("test", root,
                                     local_images=["/home/blackdeer/Desktop/conv_2.png"],
                                     url_scrapper=get_image_links, show_image_width=300,
                                     on_closing_action=get_chosen_urls, timeout=0.2, max_request_tries=1))
    root.mainloop()
