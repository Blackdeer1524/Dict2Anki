import re
from enum import IntEnum

LETTERS = set("abcdefghijklmnopqrstuvwxyz")


class SearchType(IntEnum):
    EXACT = 0
    FORWARD = 1
    BACKWARD = 2
    EVERYWHERE = 3


def get_search_pattern(query: str,
                       search_type: SearchType=SearchType.EVERYWHERE,
                       case_sensitive: bool=True) -> re.Pattern:
    query = query.strip()
    if search_type == SearchType.EXACT:
        search_pattern = r"\b{}\b".format(query)
    elif search_type == SearchType.FORWARD:
        search_pattern = r"\b{}".format(query)
    elif search_type == SearchType.BACKWARD:
        search_pattern = r"{}\b".format(query)
    else:
        search_pattern = r"{}".format(query)

    if not case_sensitive:
        pattern = re.compile(search_pattern, re.IGNORECASE)
    else:
        pattern = re.compile(search_pattern)
    return pattern


def remove_special_chars(text, sep=" ", special_chars='№!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '):
    """
    :param text: to to clean
    :param sep: replacement for special chars
    :param special_chars: special characters to remove
    :return:
    """
    new_text = ""
    start_index = 0
    while start_index < len(text) and text[start_index] in special_chars:
        start_index += 1

    while start_index < len(text):
        if text[start_index] in special_chars:
            while text[start_index] in special_chars:
                start_index += 1
                if start_index >= len(text):
                    return new_text
            new_text += sep
        new_text += text[start_index]
        start_index += 1
    return new_text.strip(sep)
