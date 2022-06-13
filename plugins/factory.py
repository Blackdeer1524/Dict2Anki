import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable
from typing import ClassVar
from typing import TypeVar, Generic

import parsers.image_parsers
import parsers.local_audio_getters
import parsers.sentence_parsers
import parsers.word_parsers.local
import parsers.word_parsers.web
import saving.card_processors
import saving.format_processors
import themes
from consts.paths import LOCAL_MEDIA_DIR
from plugins.containers import CardProcessorContainer
from plugins.containers import DeckSavingFormatContainer
from plugins.containers import ImageParserContainer
from plugins.containers import LocalAudioGetterContainer
from plugins.containers import LocalWordParserContainer
from plugins.containers import ThemeContainer
from plugins.containers import WebSentenceParserContainer
from plugins.containers import WebWordParserContainer
from plugins.exceptions import LoaderError
from plugins.exceptions import UnknownPluginName
from utils.cards import WebCardGenerator, LocalCardGenerator
from utils.storages import FrozenDict


def parse_namespace(namespace) -> dict:
    def iter_namespace(ns_pkg):
        # Specifying the second argument (prefix) to iter_modules makes the
        # returned name an absolute name instead of a relative one. This allows
        # import_module to work without having to do additional modification to
        # the name.
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

    res = {}
    for finder, name, ispkg in iter_namespace(namespace):
        parser_trunc_name = name.split(sep=".")[-1]
        res[parser_trunc_name] = importlib.import_module(name)
    return res


PluginContainer = TypeVar("PluginContainer")


@dataclass(init=False, frozen=True)
class PluginLoader(Generic[PluginContainer]):
    plugin_type: str
    _loaded_plugin_data: FrozenDict[str, PluginContainer]
    not_loaded: tuple[str]

    _already_initialized: ClassVar[set[str]] = set()

    def __init__(self,
                 plugin_type: str,
                 module: ModuleType,
                 container_type: PluginContainer,
                 error_callback: Callable[[Exception, str], None] = lambda *_: None):
        if (module_name := module.__name__) in PluginLoader._already_initialized:
            raise LoaderError(f"{module_name} loader was created earlier!")
        PluginLoader._already_initialized.add(module_name)
        super().__setattr__("plugin_type", plugin_type)

        _loaded_plugin_data = {}
        not_loaded = []
        for name, module in parse_namespace(module).items():
            try:
                _loaded_plugin_data[name] = container_type(name, module)
            except AttributeError as e:
                error_callback(e, name)
                not_loaded.append(name)
        super().__setattr__("_loaded_plugin_data", FrozenDict(_loaded_plugin_data))
        super().__setattr__("not_loaded", tuple(not_loaded))

    @property
    def loaded(self):
        return tuple(self._loaded_plugin_data)

    def get(self, name: str) -> PluginContainer:
        if (value := self._loaded_plugin_data.get(name)) is not None:
            return value
        raise UnknownPluginName(f"Unknown {self.plugin_type}: {name}")


@dataclass(init=False, frozen=True, repr=False)
class PluginFactory:
    _is_initialized:     ClassVar[bool] = False

    themes:              PluginLoader[ThemeContainer]
    web_word_parsers:    PluginLoader[WebWordParserContainer]
    local_word_parsers:  PluginLoader[LocalWordParserContainer]
    web_sent_parsers:    PluginLoader[WebSentenceParserContainer]
    image_parsers:       PluginLoader[ImageParserContainer]
    card_processors:     PluginLoader[CardProcessorContainer]
    deck_saving_formats: PluginLoader[DeckSavingFormatContainer]
    local_audio_getters: PluginLoader[LocalAudioGetterContainer]

    def __init__(self):
        if PluginFactory._is_initialized:
            raise LoaderError(f"{self.__class__.__name__} already exists!")
        PluginFactory._is_initialized = True

        super().__setattr__("themes",              PluginLoader(plugin_type="theme",
                                                                module=themes,
                                                                container_type=ThemeContainer))
        super().__setattr__("web_word_parsers",    PluginLoader(plugin_type="web word parser",
                                                                module=parsers.word_parsers.web,
                                                                container_type=WebWordParserContainer))
        super().__setattr__("local_word_parsers",  PluginLoader(plugin_type="local word parser",
                                                                module=parsers.word_parsers.local,
                                                                container_type=LocalWordParserContainer))
        super().__setattr__("web_sent_parsers",    PluginLoader(plugin_type="web sentence parser",
                                                                module=parsers.sentence_parsers,
                                                                container_type=WebSentenceParserContainer))
        super().__setattr__("image_parsers",       PluginLoader(plugin_type="web image parser",
                                                                module=parsers.image_parsers,
                                                                container_type=ImageParserContainer))
        super().__setattr__("card_processors",     PluginLoader(plugin_type="card processor",
                                                                module=saving.card_processors,
                                                                container_type=CardProcessorContainer))
        super().__setattr__("deck_saving_formats", PluginLoader(plugin_type="deck saving format",
                                                                module=saving.format_processors,
                                                                container_type=DeckSavingFormatContainer))
        super().__setattr__("local_audio_getters", PluginLoader(plugin_type="local audio getter",
                                                                module=parsers.local_audio_getters,
                                                                container_type=LocalAudioGetterContainer))

    def get_theme(self, name: str) -> ThemeContainer:
        if (theme := self.themes.get(name)) is None:
            raise UnknownPluginName(f"Unknown theme: {name}")
        return theme

    def get_web_card_generator(self, name: str) -> WebCardGenerator:
        if (args := self.web_word_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown WebCardGenerator: {name}")
        return WebCardGenerator(parsing_function=args.define,
                                item_converter=args.translate)

    def get_local_card_generator(self, name: str) -> LocalCardGenerator:
        if (args := self.local_word_parsers.get(name)) is None:
            raise UnknownPluginName(f"Unknown LocalCardGenerator: {name}")
        return LocalCardGenerator(local_dict_path=f"{LOCAL_MEDIA_DIR}/{args.local_dict_name}.json",
                                  item_converter=args.translate)

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
            raise UnknownPluginName(f"Unknown deck saving format: {name}")
        return saving_format
    
    def get_local_audio_getter(self, name: str) -> LocalAudioGetterContainer:
        if (getter := self.local_audio_getters.get(name)) is None:
            raise UnknownPluginName(f"Unknown local audio getter: {name}")
        return getter
    
        
    
plugins = PluginFactory()
