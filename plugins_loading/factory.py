import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable
from typing import ClassVar
from typing import TypeVar, Generic

import plugins.language_packages
import plugins.parsers.audio_getters.local
import plugins.parsers.audio_getters.web
import plugins.parsers.image_parsers
import plugins.parsers.sentence_parsers
import plugins.parsers.word_parsers.local
import plugins.parsers.word_parsers.web
import plugins.saving.card_processors
import plugins.saving.format_processors
import plugins.themes
from plugins_loading.containers import CardProcessorContainer
from plugins_loading.containers import DeckSavingFormatContainer
from plugins_loading.containers import ImageParserContainer
from plugins_loading.containers import LanguagePackageContainer
from plugins_loading.containers import LocalAudioGetterContainer
from plugins_loading.containers import WebAudioGetterContainer
from plugins_loading.containers import LocalWordParserContainer
from plugins_loading.containers import ThemeContainer
from plugins_loading.containers import WebSentenceParserContainer
from plugins_loading.containers import WebWordParserContainer
from plugins_loading.exceptions import LoaderError
from plugins_loading.exceptions import UnknownPluginName


def parse_namespace(namespace, postfix: str = "") -> dict:
    def iter_namespace(ns_pkg):
        # Specifying the second argument (prefix) to iter_modules makes the
        # returned name an absolute name instead of a relative one. This allows
        # import_module to work without having to do additional modification to
        # the name.
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

    res = {}
    for finder, name, ispkg in iter_namespace(namespace):
        parser_trunc_name = name.split(sep=".")[-1]
        res[parser_trunc_name] = importlib.import_module(name + postfix)
    return res


PluginContainer = TypeVar("PluginContainer")


@dataclass(slots=True, init=False, frozen=True)
class PluginLoader(Generic[PluginContainer]):
    plugin_type: str
    _loaded_plugin_data: dict[str, PluginContainer]
    not_loaded: tuple[str]

    _already_initialized: ClassVar[set[str]] = set()

    def __init__(self,
                 plugin_type: str,
                 module: ModuleType,
                 configurable: bool,
                 container_type: PluginContainer,
                 error_callback: Callable[[Exception, str], None] = lambda *_: None):
        if (module_name := module.__name__) in PluginLoader._already_initialized:
            raise LoaderError(f"{module_name} loader was created earlier!")
        PluginLoader._already_initialized.add(module_name)
        object.__setattr__(self, "plugin_type", plugin_type)

        _loaded_plugin_data = {}
        not_loaded = []
        namespace_parsed_results = parse_namespace(module, postfix=".main") if configurable else parse_namespace(module)
        for name, module in namespace_parsed_results.items():
            try:
                _loaded_plugin_data[name] = container_type(name, module)
            except AttributeError as e:
                error_callback(e, name)
                not_loaded.append(name)
        object.__setattr__(self, "_loaded_plugin_data", _loaded_plugin_data)
        object.__setattr__(self, "not_loaded", tuple(not_loaded))

    @property
    def loaded(self):
        return tuple(self._loaded_plugin_data)

    def get(self, name: str) -> PluginContainer:
        if (value := self._loaded_plugin_data.get(name)) is not None:
            return value
        raise UnknownPluginName(f"Unknown {self.plugin_type}: {name}")


@dataclass(slots=True, init=False, frozen=True, repr=False)
class PluginFactory:
    _is_initialized:     ClassVar[bool] = False

    language_packages:   PluginLoader[LanguagePackageContainer]
    themes:              PluginLoader[ThemeContainer]
    web_word_parsers:    PluginLoader[WebWordParserContainer]
    local_word_parsers:  PluginLoader[LocalWordParserContainer]
    web_sent_parsers:    PluginLoader[WebSentenceParserContainer]
    image_parsers:       PluginLoader[ImageParserContainer]
    card_processors:     PluginLoader[CardProcessorContainer]
    deck_saving_formats: PluginLoader[DeckSavingFormatContainer]
    local_audio_getters: PluginLoader[LocalAudioGetterContainer]
    web_audio_getters:   PluginLoader[WebAudioGetterContainer]

    def __init__(self):
        if PluginFactory._is_initialized:
            raise LoaderError(f"{self.__class__.__name__} already exists!")
        PluginFactory._is_initialized = True
        object.__setattr__(self, "language_packages",   PluginLoader(plugin_type="language package",
                                                                     module=plugins.language_packages,
                                                                     configurable=False,
                                                                     container_type=LanguagePackageContainer))
        object.__setattr__(self, "themes",              PluginLoader(plugin_type="theme",
                                                                     module=plugins.themes,
                                                                     configurable=False,
                                                                     container_type=ThemeContainer))
        object.__setattr__(self, "web_word_parsers",    PluginLoader(plugin_type="web word parser",
                                                                     module=plugins.parsers.word_parsers.web,
                                                                     configurable=True,
                                                                     container_type=WebWordParserContainer))
        object.__setattr__(self, "local_word_parsers",  PluginLoader(plugin_type="local word parser",
                                                                     module=plugins.parsers.word_parsers.local,
                                                                     configurable=True,
                                                                     container_type=LocalWordParserContainer))
        object.__setattr__(self, "web_sent_parsers",    PluginLoader(plugin_type="web sentence parser",
                                                                     module=plugins.parsers.sentence_parsers,
                                                                     configurable=True,
                                                                     container_type=WebSentenceParserContainer))
        object.__setattr__(self, "image_parsers",       PluginLoader(plugin_type="web image parser",
                                                                     module=plugins.parsers.image_parsers,
                                                                     configurable=True,
                                                                     container_type=ImageParserContainer))
        object.__setattr__(self, "card_processors",     PluginLoader(plugin_type="card processor",
                                                                     module=plugins.saving.card_processors,
                                                                     configurable=False,
                                                                     container_type=CardProcessorContainer))
        object.__setattr__(self, "deck_saving_formats", PluginLoader(plugin_type="deck plugins.saving format",
                                                                     module=plugins.saving.format_processors,
                                                                     configurable=False,
                                                                     container_type=DeckSavingFormatContainer))
        object.__setattr__(self, "local_audio_getters", PluginLoader(plugin_type="local audio getter",
                                                                     module=plugins.parsers.audio_getters.local,
                                                                     configurable=True,
                                                                     container_type=LocalAudioGetterContainer))
        object.__setattr__(self, "web_audio_getters",   PluginLoader(plugin_type="web audio getter",
                                                                     module=plugins.parsers.audio_getters.web,
                                                                     configurable=True,
                                                                     container_type=WebAudioGetterContainer))

    def get_language_package(self, name: str) -> LanguagePackageContainer:
        if (lang_pack := self.language_packages.get(name)) is None:
            raise UnknownPluginName(f"Unknown language package: {name}")
        return lang_pack

    def get_theme(self, name: str) -> ThemeContainer:
        if (theme := self.themes.get(name)) is None:
            raise UnknownPluginName(f"Unknown theme: {name}")
        return theme

    def get_web_word_parser(self, name: str) -> WebWordParserContainer:
        if (web_parser := self.web_word_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown WebCardGenerator: {name}")
        return web_parser

    def get_local_word_parser(self, name: str) -> LocalWordParserContainer:
        if (local_parser := self.local_word_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown LocalCardGenerator: {name}")
        return local_parser

    def get_sentence_parser(self, name: str) -> WebSentenceParserContainer:
        if (gen := self.web_sent_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown sentence parser: {name}")
        return gen

    def get_image_parser(self, name: str) -> ImageParserContainer:
        if (gen := self.image_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown image parser: {name}")
        return gen

    def get_card_processor(self, name: str) -> CardProcessorContainer:
        if (proc := self.card_processors.get(name)) is None:
            raise UnknownPluginName(f"Unknown card processor: {name}")
        return proc
    
    def get_deck_saving_formats(self, name: str) -> DeckSavingFormatContainer:
        if (saving_format := self.deck_saving_formats.get(name)) is None:
            raise UnknownPluginName(f"Unknown deck plugins.saving format: {name}")
        return saving_format
    
    def get_local_audio_getter(self, name: str) -> LocalAudioGetterContainer:
        if (getter := self.local_audio_getters.get(name)) is None:
            raise UnknownPluginName(f"Unknown local audio getter: {name}")
        return getter

    def get_web_audio_getter(self, name: str) -> WebAudioGetterContainer:
        if (getter := self.web_audio_getters.get(name)) is None:
            raise UnknownPluginName(f"Unknown web audio getter: {name}")
        return getter


loaded_plugins = PluginFactory()
