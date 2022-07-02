from typing import NamedTuple


__all__ = ["FIELDS"]


class _CardFields(NamedTuple):
    word: str = "word"
    special: str = "special"
    definition: str = "definition"
    sentences: str = "examples"
    img_links: str = "image_links"
    audio_links: str = "audio_links"
    dict_tags: str = "tags"


FIELDS = _CardFields()
