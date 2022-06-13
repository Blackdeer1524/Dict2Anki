from typing import Protocol, Callable
from plugins.parsers.return_types import SentenceGenerator, ImageGenerator
from utils.cards import SavedDataDeck, CardStatus


class ThemeInterface(Protocol):
    label_cfg: dict
    button_cfg: dict
    text_cfg: dict
    entry_cfg: dict
    checkbutton_cfg: dict
    toplevel_cfg: dict
    root_cfg: dict
    frame_cfg: dict
    option_menu_cfg: dict
    option_submenus_cfg: dict


class WebWordParserInterface(Protocol):
    @staticmethod
    def define(word: str) -> dict:
        ...

    @staticmethod
    def translate(word: str, word_dict: dict) -> dict:
        ...


class LocalWordParserInterface(Protocol):
    DICTIONARY_PATH: str

    @staticmethod
    def translate(word: str, word_dict: dict) -> dict:
        ...


class WebSentenceParserInterface(Protocol):
    @staticmethod
    def get_sentence_batch(word: str, size: int) -> SentenceGenerator:
        ...


class ImageParserInterface(Protocol):
    @staticmethod
    def get_image_links(word: str) -> ImageGenerator:
        ...


class CardProcessorInterface(Protocol):
    @staticmethod
    def get_save_image_name(word: str, image_source: str, image_parser_name: str, dict_tags: dict) -> str:
        ...

    @staticmethod
    def get_card_image_name(saved_image_path: str) -> str:
        ...

    @staticmethod
    def get_save_audio_name(word: str, audio_provider: str, multiple_postfix: str,
                            dict_tags: dict) -> str:
        ...

    @staticmethod
    def get_card_audio_name(saved_audio_path: str) -> str:
        ...

    @staticmethod
    def process_card(card: dict) -> None:
        ...


class DeckSavingFormatInterface(Protocol):
    @staticmethod
    def save(deck: SavedDataDeck, saving_card_status: CardStatus, saving_path: str,
             image_names_wrapper: Callable[[str], str],
             audio_names_wrapper: Callable[[str], str]):
        ...


class LocalAudioGetterInterface(Protocol):
    AUDIO_FOLDER: str

    @staticmethod
    def get_local_audios(word: str, dict_tags: dict) -> list[str]:
        ...
