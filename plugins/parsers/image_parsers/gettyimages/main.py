import os
import re

import bs4
import requests
from plugins_management.config_management import Config
from plugins_management.parsers_return_types import ImageGenerator

FILE_PATH = os.path.basename(__file__)

CONFIG_DOCS = """
"""

_CONF_VALIDATION_SCHEME = {}

config = Config(validation_scheme=_CONF_VALIDATION_SCHEME)


def get_image_links(word: str) -> ImageGenerator:
    user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/70.0.3538.67 Safari/537.36"
    headers = {'User-Agent': user_agent}
    link = "https://www.gettyimages.com/photos/{}".format(word)
    try:
        r = requests.get(link, headers=headers, timeout=5)
        r.raise_for_status()
    except Exception:
        return [], f"{FILE_PATH} couldn't get a web page!"

    soup = bs4.BeautifulSoup(r.content, "html.parser")
    gallery = soup.find("div", {"class": re.compile("GalleryItems-module__searchContent")})
    if gallery is None:
        return [], f"{FILE_PATH} couldn't parse a web page!"

    images = [] if gallery is None else gallery.find_all("div",
                                                         {"class": re.compile("MosaicAsset-module__galleryMosaicAsset")})
    batch_size = yield
    results = []
    for ind, image_block in enumerate(images):
        found = image_block.find("a", {"class": re.compile("MosaicAsset-module__link")})
        if found is not None:
            preview_image_link = found.get("href")
            if preview_image_link is not None:
                split_preview_image_link = preview_image_link.split("/")
                image_name, image_id = split_preview_image_link[-2], split_preview_image_link[-1]
                image_link = f"https://media.gettyimages.com/photos/{image_name}-id{image_id}"
                results.append(image_link)
        if not ind % batch_size:
            batch_size = yield results, ""
            results = []
    return results, ""


if __name__ == "__main__":
    from pprint import pprint

    image_url_gen = get_image_links("do")
    try:
        next(image_url_gen)
        while True:
            urls, error_message = image_url_gen.send(1)
            pprint(urls)
    except StopIteration as exception:
        pprint(exception.value)