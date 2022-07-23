"""
Credits:
    https://github.com/Rascalov/Anki-Simple-Forvo-Audio
"""


import requests.utils

from plugins_management.config_management import LoadableConfig
from .consts import _PLUGIN_NAME, _PLUGIN_LOCATION
from .page_processing import get_forvo_page, get_audio_link

_CONFIG_DOCS = """
language_code
    audio language to fetch
    type: string

timeout
    request timeout in seconds.
    default value: 1
"""

_VALIDATION_SCHEME = {
    "language_code": ("en", [str], []),
    "timeout": (1, [int, float], [])
}

config = LoadableConfig(config_location=_PLUGIN_LOCATION,
                validation_scheme=_VALIDATION_SCHEME,
                docs=_CONFIG_DOCS)


def get_web_audios(word: str, dict_tags: dict) -> tuple[tuple[list[str], list[str]], str]:
    audio_links = []
    additional_info = []
    wordEncoded = requests.utils.requote_uri(word)
    forvoPage, error_message = get_forvo_page("https://forvo.com/word/" + wordEncoded, timeout=config["timeout"])
    if error_message:
        return ([], []), error_message
    speachSections = forvoPage.select("div#language-container-" + config["language_code"])
    if not len(speachSections):
        return ([], []), f"[{_PLUGIN_NAME}] Word not found (Language Container does not exist!)"
    speachSections = forvoPage.select_one("div#language-container-" + config["language_code"])
    audioListUl = speachSections.select_one("ul")
    if audioListUl is None or not len(audioListUl.findChildren(recursive=False)):
        return ([], []), f"[{_PLUGIN_NAME}] Word not found (Language Container exists, but audio not found)"
    if(config["language_code"] == "en"):
        audioListLis = forvoPage.select("li[class*=en_]")
    else:
        audioListLis = audioListUl.find_all("li", attrs={'class': None})
    for li in audioListLis:
        if (r := li.find("div")) is not None and (onclick := r.get("onclick")) is not None:
            audio_links.append(get_audio_link(onclick))
            additional_info.append(li.get("class", ""))
    return (audio_links, additional_info), ""
