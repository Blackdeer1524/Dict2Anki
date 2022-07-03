import os
from plugins_management.config_management import Config
from app_utils.preprocessing import remove_empty_keys
from consts.card_fields import FIELDS

DICTIONARY_PATH = "wordset"
SCHEME_DOCS = """
tags: {
    pos: part of speach (str)
    domain: word domain (list[str])
    level: English proficiency level (str)[A1, A2, B1, B2, C1, C2]
    region: where this word mostly in use (list[str])
    usage: usage context (list[str])
}
"""

_CONF_VALIDATION_SCHEME = {}

config = Config(config_location=os.path.dirname(__file__),
                validation_scheme=_CONF_VALIDATION_SCHEME,
                docs="")


def translate(word: str, word_dict: dict):
    word_list = []
    for pos in word_dict:
        # uk_ipa = word_dict[word][pos]["UK IPA"]
        # us_ipa = word_dict[word][pos]["US IPA"]
        for name in ("examples", "domain", "labels_and_codes", "level", "region", "usage"):
            if word_dict[pos].get(name) is None:
                word_dict[pos][name] = []
            while len(word_dict[pos]["definitions"]) > len(word_dict[pos][name]):
                word_dict[pos][name].append([])

        for definition, examples, domain, labels_and_codes, level, \
            region, usage in zip(word_dict[pos]["definitions"],
                                 word_dict[pos]["examples"],
                                 word_dict[pos]["domain"],
                                 word_dict[pos]["labels_and_codes"],
                                 word_dict[pos]["level"],
                                 word_dict[pos]["region"],
                                 word_dict[pos]["usage"]):
            current_word_dict = {FIELDS.word: word.strip(),
                                 FIELDS.definition: definition,
                                 FIELDS.sentences: examples,
                                 FIELDS.dict_tags: {"domain": domain,
                                                    "level": level,
                                                    "region": region,
                                                    "usage": usage,
                                                    "pos": pos
                                                    }
                                 }
            remove_empty_keys(current_word_dict)
            word_list.append(current_word_dict)
    return word_list
