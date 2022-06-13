import os

from consts.paths import LOCAL_MEDIA_DIR
from utils.string_utils import remove_special_chars

LETTERS = frozenset("abcdefghijklmnopqrstuvwxyz")
AUDIO_NAME_SPEC_CHARS = '/\\:*?\"<>| '
AUDIO_FOLDER = "us_audios"


def get_local_audios(word, dict_tags: dict) -> list[str]:
    word = word.strip()
    if not word:
        return []

    letter_group = word[0] if word[0].lower() in LETTERS else "0-9"
    name = f"{remove_special_chars(word, '-', AUDIO_NAME_SPEC_CHARS)}.mp3"
    search_root = os.path.join(LOCAL_MEDIA_DIR, AUDIO_FOLDER, letter_group)

    for current_dir_path, dirs, files in os.walk(search_root):
        if name in files:
            return [os.path.join(str(current_dir_path), name)]
        elif name in dirs:
            dir = os.path.join(str(current_dir_path), name)
            return [file_path for item in os.listdir(dir)
                    if os.path.isfile((file_path := os.path.join(dir, item)))]
    return []
