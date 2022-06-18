import os
import re

import bs4
import requests

from plugins.parsers.return_types import SentenceGenerator

FILE_PATH = os.path.basename(__file__)


def get_sentence_batch(word: str, size: int = 5) -> SentenceGenerator:
    re_pattern = re.compile("^(.?\d+.? )")
    try:
        page = requests.get(f"https://searchsentences.com/words/{word}-in-a-sentence",
                            timeout=5)
        page.raise_for_status()
    except requests.RequestException as e:
        yield [], f"{FILE_PATH} couldn't get a web page: {e}"
        return

    soup = bs4.BeautifulSoup(page.content, "html.parser")
    src = soup.find_all("li", {"class": "sentence-row"})
    sentences = []
    for sentence_block in src:
        if (sentence := sentence_block.find("span")) is None:
            continue

        text = sentence.get_text()
        if text:
            text = re.sub(re_pattern, "", text.strip())
            sentences.append(text)

    sentences.sort(key=len)
    for i in range(0, len(sentences), size):
        yield sentences[i:i + size], ""
