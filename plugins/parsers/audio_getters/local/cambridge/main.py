import os

from app_utils.string_utils import remove_special_chars
from consts.paths import LOCAL_MEDIA_DIR
from plugins_management.config_management import LoadableConfig

_CONFIG_DOCS = \
"""
type: 
    Audio region 
    valid values: either of ["uk", "us"] 

pos_search:
    Whether to search audio by Part Of Speach (pos) or not
    valid values: (true, false) 
"""


_CONF_VALIDATION_SCHEME = \
    {
        "audio_region": ("us", [str], ["us", "uk"]),
        "pos_search": (False, [bool], [])
    }

config = LoadableConfig(config_location=os.path.dirname(__file__),
                validation_scheme=_CONF_VALIDATION_SCHEME,
                docs=_CONFIG_DOCS)

_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyz")
_AUDIO_NAME_SPEC_CHARS = '/\\:*?\"<>| '


def get_local_audios(word, dict_tags: dict) -> list[str]:
    word = word.strip()
    if not word:
        return []

    audio_folder = f"{config['audio_region']}_audios"

    letter_group = word[0] if word[0].lower() in _LETTERS else "0-9"
    name = f"{remove_special_chars(word, '-', _AUDIO_NAME_SPEC_CHARS)}.mp3"
    search_root = os.path.join(LOCAL_MEDIA_DIR, audio_folder, letter_group)

    if config["pos_search"]:
        pos = remove_special_chars(dict_tags.get("pos", "").lower(), '-', _AUDIO_NAME_SPEC_CHARS)
        res = os.path.join(search_root, pos, name)
        if os.path.exists(res):
            if os.path.isfile(res):
                return [res]
            if os.path.isdir(res):
                return [str(file_path) for item in os.listdir(res)
                        if os.path.isfile((file_path := os.path.join(res, item)))]
        return []

    for current_dir_path, dirs, files in os.walk(search_root):
        if name in files:
            return [os.path.join(str(current_dir_path), name)]
        elif name in dirs:
            dir = os.path.join(str(current_dir_path), name)
            return [file_path for item in os.listdir(dir)
                    if os.path.isfile((file_path := os.path.join(dir, item)))]
    return []
