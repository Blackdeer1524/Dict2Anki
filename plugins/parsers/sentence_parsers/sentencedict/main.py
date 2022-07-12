import os
import re

import bs4
import requests
from plugins_management.config_management import LoadableConfig
from plugins_management.parsers_return_types import SentenceGenerator

FILE_PATH = os.path.split(os.path.dirname(__file__))[-1]

_CONF_VALIDATION_SCHEME = {
    "timeout": (1, [int, float], [])
}

_CONF_DOCS = """
timeout:
    Request timeout in seconds
    type: integer, float
    default value: 1
"""

config = LoadableConfig(config_location=os.path.dirname(__file__),
                        validation_scheme=_CONF_VALIDATION_SCHEME,
                        docs=_CONF_DOCS)


def get_sentence_batch(word: str, size: int = 5) -> SentenceGenerator:
    re_pattern = re.compile("^(.?\d+.? )")

    try:
        page = requests.get(f"https://sentencedict.com/{word}.html",
                            timeout=config["timeout"])
        page.raise_for_status()
    except requests.RequestException as e:
        yield [], f"{FILE_PATH} couldn't get a web page: {e}"
        return

    soup = bs4.BeautifulSoup(page.content, "html.parser")
    sentences_block = soup.find("div", {"id": "all"})
    if sentences_block is None:
        yield [], f"{FILE_PATH} couldn't parse a web page!"
        return

    sentences_block = sentences_block.find_all("div")
    sentences = []
    for sentence in sentences_block:
        if sentence is not None:
            text = sentence.get_text()
            if text:
                text = re.sub(re_pattern, "", text.strip())
                sentences.append(text)

    sentences.sort(key=len)
    for i in range(0, len(sentences), size):
        yield sentences[i:i + size], ""
