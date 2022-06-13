from dataclasses import dataclass
from typing import Callable

from plugins.parsers.return_types import SentenceGenerator, ImageGenerator
from plugins_management.interfaces import ThemeInterface
from plugins_management.interfaces import CardProcessorInterface
from plugins_management.interfaces import DeckSavingFormatInterface
from plugins_management.interfaces import ImageParserInterface
from plugins_management.interfaces import LocalAudioGetterInterface
from plugins_management.interfaces import LocalWordParserInterface
from plugins_management.interfaces import WebSentenceParserInterface
from plugins_management.interfaces import WebWordParserInterface
from utils.cards import CardStatus
from utils.cards import SavedDataDeck


@dataclass(init=False, repr=False, frozen=True, eq=False, order=False)
class _PluginContainer:
    name: str
    
    def __init__(self, name: str):
        super().__setattr__("name", name)


class ThemeContainer(_PluginContainer):
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

    def __init__(self, name: str, source_module: ThemeInterface):
        super(ThemeContainer, self).__init__(name)
        super().__setattr__("label_cfg",           source_module.label_cfg)
        super().__setattr__("button_cfg",          source_module.button_cfg)
        super().__setattr__("text_cfg",            source_module.text_cfg)
        super().__setattr__("entry_cfg",           source_module.entry_cfg)
        super().__setattr__("checkbutton_cfg",     source_module.checkbutton_cfg)
        super().__setattr__("toplevel_cfg",        source_module.toplevel_cfg)
        super().__setattr__("root_cfg",            source_module.root_cfg)
        super().__setattr__("frame_cfg",           source_module.frame_cfg)
        super().__setattr__("option_menu_cfg",     source_module.option_menu_cfg)
        super().__setattr__("option_submenus_cfg", source_module.option_submenus_cfg)


class WebWordParserContainer(_PluginContainer):
    define: Callable[[str], list[(str, dict)]]
    translate: Callable[[str, dict], dict]

    def __init__(self, name: str, source_module: WebWordParserInterface):
        super(WebWordParserContainer, self).__init__(name)
        super().__setattr__("define", source_module.define)
        super().__setattr__("translate", source_module.translate)


class LocalWordParserContainer(_PluginContainer):
    local_dict_name: str
    translate: Callable[[str], dict]

    def __init__(self, name: str, source_module: LocalWordParserInterface):
        super(LocalWordParserContainer, self).__init__(name)
        super().__setattr__("local_dict_name", source_module.DICTIONARY_PATH)
        super().__setattr__("translate", source_module.translate)


class WebSentenceParserContainer(_PluginContainer):
    get_sentence_batch: Callable[[str, int], SentenceGenerator]

    def __init__(self, name: str, source_module: WebSentenceParserInterface):
        super(WebSentenceParserContainer, self).__init__(name)
        super().__setattr__("get_sentence_batch", source_module.get_sentence_batch)


class ImageParserContainer(_PluginContainer):
    get_image_links: Callable[[str], ImageGenerator]

    def __init__(self, name: str, source_module: ImageParserInterface):
        super(ImageParserContainer, self).__init__(name)
        super().__setattr__("get_image_links", source_module.get_image_links)


class CardProcessorContainer(_PluginContainer):
    get_save_image_name: Callable[[str, str, dict], str]
    get_card_image_name: Callable[[str], str]
    get_save_audio_name: Callable[[str, str, str, dict], str]
    get_card_audio_name: Callable[[str], str]
    process_card:        Callable[[dict], None]

    def __init__(self, name: str, source_module: CardProcessorInterface):
        super(CardProcessorContainer, self).__init__(name)
        super().__setattr__("get_save_image_name", source_module.get_save_image_name)
        super().__setattr__("get_card_image_name", source_module.get_card_image_name)
        super().__setattr__("get_save_audio_name", source_module.get_save_audio_name)
        super().__setattr__("get_card_audio_name", source_module.get_card_audio_name)
        super().__setattr__("process_card",        source_module.process_card)


class DeckSavingFormatContainer(_PluginContainer):
    save: Callable[[SavedDataDeck, CardStatus, str, Callable[[str], str], Callable[[str], str]], None]

    def __init__(self, name: str, source_module: DeckSavingFormatInterface):
        super(DeckSavingFormatContainer, self).__init__(name)
        super().__setattr__("save", source_module.save)


class LocalAudioGetterContainer(_PluginContainer):
    get_local_audios: Callable[[str, dict], str]

    def __init__(self, name: str, source_module: LocalAudioGetterInterface):
        super(LocalAudioGetterContainer, self).__init__(name)
        super().__setattr__("get_local_audios", source_module.get_local_audios)
