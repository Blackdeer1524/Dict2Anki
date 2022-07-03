import os
from app_utils.preprocessing import remove_empty_keys
from consts.card_fields import FIELDS
from plugins_management.config_management import Config
from .utils import define as _define

SCHEME_DOCS = """
tags: {
    pos: part of speach (str)
    domain: word domain (list[str])
    level: English proficiency level (str)["A1", "A2", "B1", "B2", "C1", "C2"]
    region: where this word mostly in use (list[str])
    usage: usage context (list[str])
}
"""

CONFIG_DOCS = """
audio_region:
    Audio region 
    valid values: either of ["uk", "us"] 
"""


_CONF_VALIDATION_SCHEME = \
    {
        "audio_region": ("us", (str,), ("us", "uk")),
    }

config = Config(config_location=os.path.dirname(__file__), validation_scheme=_CONF_VALIDATION_SCHEME)


def translate(word: str, word_dict: dict):
    audio_region_field = f"{config['audio_region'].upper()}__audio_link"
    word_list = []
    for pos in word_dict:
        audio = word_dict[pos].get(audio_region_field, [])
        for definition, examples, domain, labels_and_codes, level, \
            region, usage, image, alt_terms, irreg_forms \
                in zip(word_dict[pos]["definitions"],
                       word_dict[pos]["examples"],
                       word_dict[pos]["domain"],
                       word_dict[pos]["labels_and_codes"],
                       word_dict[pos]["level"],
                       word_dict[pos]["region"],
                       word_dict[pos]["usage"],
                       word_dict[pos]["image_links"],
                       word_dict[pos]["alt_terms"],
                       word_dict[pos]["irregular_forms"]):
            current_word_dict = {FIELDS.word: word.strip(),
                                 FIELDS.special: irreg_forms + alt_terms,
                                 FIELDS.definition: definition,
                                 FIELDS.sentences: examples,
                                 FIELDS.audio_links: audio,
                                 FIELDS.img_links: [image] if image else [],
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


def define(word: str) -> list[tuple[str, dict]]:
    return _define(word=word)
