import os

from consts.paths import LOCAL_MEDIA_DIR
from utils.string_utils import remove_special_chars

LETTERS = frozenset("abcdefghijklmnopqrstuvwxyz")
AUDIO_NAME_SPEC_CHARS = '/\\:*?\"<>| '
AUDIO_FOLDER = "uk_audios"


def get_local_audios(word, dict_tags: dict) -> list[str]:
    word = word.strip()
    pos = dict_tags.get("pos", "")
    if not word or not pos:
        return []

    letter_group = word[0] if word[0].lower() in LETTERS else "0-9"
    name = f"{remove_special_chars(word, '-', AUDIO_NAME_SPEC_CHARS)}.mp3"
    search_root = os.path.join(LOCAL_MEDIA_DIR, AUDIO_FOLDER, letter_group)
    pos = remove_special_chars(pos.lower(), '-', AUDIO_NAME_SPEC_CHARS)
    res = os.path.join(search_root, pos, name)
    if os.path.exists(res):
        if os.path.isfile(res):
            return [res]

        if os.path.isdir(res):
            return [str(file_path) for item in os.listdir(res)
                    if os.path.isfile((file_path := os.path.join(res, item)))]
    return []
