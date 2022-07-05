import base64
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .consts import _HEADERS, _PLUGIN_NAME


def get_forvo_page(url: str, timeout: int = 1) -> tuple[Optional[BeautifulSoup], str]:
    try:
        r = requests.get(url, headers=_HEADERS)
        r.raise_for_status()
        decoded_page_content = r.content.decode('UTF-8')
    except requests.RequestException as e:
        return None, f"[{_PLUGIN_NAME}] Couldn't get web page! Error: {str(e)}"
    except UnicodeDecodeError as e:
        return None, f"[{_PLUGIN_NAME}] Couldn't decode page to UTF-8 format! Error: {str(e)}"

    soup = BeautifulSoup(decoded_page_content, "html.parser")
    return soup, ""


def get_audio_link(onclickFunction) -> str:
    #example js play functions from forvo:
    #Play(6166435,'OTg4MTIyMC8xMzgvOTg4MTIyMF8xMzhfMzM5MDIxLm1wMw==','OTg4MTIyMC8xMzgvOTg4MTIyMF8xMzhfMzM5MDIxLm9nZw==',false,'by80L280Xzk4ODEyMjBfMTM4XzMzOTAyMS5tcDM=','by80L280Xzk4ODEyMjBfMTM4XzMzOTAyMS5vZ2c=','h');return false;
    #Play(6687207,'OTU5NzcxMy8xMzgvOTU5NzcxM18xMzhfNjk2MDEyMi5tcDM=','OTU5NzcxMy8xMzgvOTU5NzcxM18xMzhfNjk2MDEyMi5vZ2c=',false,'','','l');return false;
    # All audios have an ogg version as a fallback on the mp3. Ogg is open source and compresses audio to a smaller size than mp3.
    # So I grab the ogg base64 string and decode it.
    base64audio = onclickFunction.split(',')[2].replace('\'', "")
    decodedLink = base64.b64decode(base64audio.encode('ascii')).decode('ascii')
    return "https://audio00.forvo.com/ogg/" + decodedLink


def get_forvo_audio_link(audioLi) -> str:
    #selector = CSSSelector("span")
    audioTag = audioLi.select_one("span")
    audioLink =  get_audio_link(audioTag["onclick"])
    return audioLink