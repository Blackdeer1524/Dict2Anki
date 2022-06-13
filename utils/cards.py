import json
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Union, Any

from consts.card_fields import FIELDS
from plugins.parsers.return_types import SentenceGenerator
from utils.storages import FrozenDictJSONEncoder
from utils.storages import PointerList, FrozenDict


class Card(FrozenDict):
    __slots__ = ()

    def __init__(self, card_fields: dict[str, Any] = None):
        if card_fields is None:
            super(Card, self).__init__(data={})
            return

        data = {}
        for field_name in FIELDS:
            if (field_value := card_fields.get(field_name)) is not None:
                data[field_name] = field_value

        super(Card, self).__init__(data=data)

    def __repr__(self):
        return f"Card {self._data}"

    @staticmethod
    def get_str_dict_tags(card_data: Union[dict, "Card"],
                          prefix: str = "",
                          sep: str = "::",
                          tag_processor: Callable[[str], str] = lambda x: x) -> str:
        if (dictionary_tags := card_data.get(FIELDS.dict_tags)) is None:
            return ""

        def traverse_tags_dict(res_container: list[str], current_item: dict, cur_stage_prefix: str = ""):
            nonlocal sep

            for key in current_item:
                cur_prefix = f"{cur_stage_prefix}{tag_processor(key)}{sep}"

                if isinstance((value := current_item[key]), dict):
                    traverse_tags_dict(res_container, value, cur_prefix)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            traverse_tags_dict(res_container, item, cur_prefix)
                        else:
                            res_container.append(f"{cur_prefix}{tag_processor(item)}")
                else:
                    res_container.append(f"{cur_prefix}{tag_processor(value)}")

        tags_container = []
        p = f"{prefix}{sep}" if prefix else ""
        traverse_tags_dict(tags_container, dictionary_tags, cur_stage_prefix=p)
        return " ".join(tags_container)


class CardGenerator(ABC):
    def __init__(self, item_converter: Callable[[str, dict], dict]):
        self.item_converter = item_converter

    @abstractmethod
    def _get_search_subset(self, query: str) -> list[tuple[str, dict]]:
        pass

    def get(self, query: str, word_filter: Callable[[str], bool],
            additional_filter: Callable[[Card], bool] = None) -> list[Card]:
        if additional_filter is None:
            additional_filter = lambda _: True

        source: list[tuple[str, dict]] = self._get_search_subset(query)
        res: list[Card] = []
        for word, word_data in source:
            if word_filter(word):
                for item in self.item_converter(word, word_data):
                    if additional_filter(card := Card(item)):
                        res.append(card)
        return res


class LocalCardGenerator(CardGenerator):
    def __init__(self,
                 local_dict_path: str,
                 item_converter: Callable[[(str, dict)], dict]):
        """
        local_dict_path: str
        item_converter: Callable[[(str, dict)], dict]
        """
        super(LocalCardGenerator, self).__init__(item_converter)
        if not os.path.isfile(local_dict_path):
            raise Exception(f"Local dictionary with path \"{local_dict_path}\" doesn't exist")

        with open(local_dict_path, "r", encoding="UTF-8") as f:
            self.local_dictionary: list[(str, dict)] = json.load(f)

    def _get_search_subset(self, query: str) -> list[tuple[str, dict]]:
        return self.local_dictionary


class WebCardGenerator(CardGenerator):
    def __init__(self,
                 parsing_function: Callable[[str], list[(str, dict)]],
                 item_converter: Callable[[(str, dict)], dict]):
        """
        parsing_function: Callable[[str], list[(str, dict)]]
        item_converter: Callable[[(str, dict)], dict]
        """
        super(WebCardGenerator, self).__init__(item_converter)
        self.parsing_function = parsing_function

    def _get_search_subset(self, query: str) -> list[tuple[str, dict]]:
        return self.parsing_function(query)


class Deck(PointerList):
    __slots__ = "deck_path", "_card_generator", "_cards_left"

    def __init__(self, deck_path: str,
                 current_deck_pointer: int,
                 card_generator: CardGenerator):
        self.deck_path = deck_path
        if os.path.isfile(self.deck_path):
            with open(self.deck_path, "r", encoding="UTF-8") as f:
                deck: list[dict[str, Union[str, dict]]] = json.load(f)
            super(Deck, self).__init__(data=deck,
                                       starting_position=min(current_deck_pointer, len(deck) - 1),
                                       default_return_value=Card())
        else:
            raise Exception("Invalid _deck path!")

        self._card_generator: CardGenerator = card_generator
        for i in range(len(self)):
            self._data[i] = Card(self._data[i])

        self._cards_left = max(0, len(self) - self._pointer_position)

    def update_card_generator(self, cd: CardGenerator):
        self._card_generator = cd

    def set_card_generator(self, value: CardGenerator):
        assert (isinstance(value, CardGenerator))
        self._card_generator = value

    def get_n_cards_left(self) -> int:
        return self._cards_left

    def move(self, n: int) -> None:
        super(Deck, self).move(n)
        self._cards_left = max(0, len(self) - self._pointer_position)

    def find_card(self, searching_func: Callable[[Card], bool]) -> PointerList:
        move_list = []
        last_found = self.get_pointer_position()
        for current_index in range(self.get_pointer_position() + 1, len(self)):
            if searching_func(self[current_index]):
                move_list.append(current_index - last_found)
                last_found = current_index
        return PointerList(data=move_list)

    def add_card_to_deck(self, query: str, **kwargs) -> int:
        res: list[Card] = self._card_generator.get(query, **kwargs)

        self._data = self[:self._pointer_position] + res + self[self._pointer_position:]
        if res:
            self._pointer_position = self._pointer_position - 1

        self._cards_left += len(res)
        return len(res)

    def append(self, card: Card):
        self._data = self[:self._pointer_position] + [card] + self[self._pointer_position:]
        self.move(1)

    def get_card(self) -> Card:
        self.move(1)
        return self.get_pointed_item()

    def get_deck(self) -> list[Card]:
        return self._data

    def save(self):
        with open(self.deck_path, "w", encoding="utf-8") as deck_file:
            json.dump(self._data, deck_file, cls=FrozenDictJSONEncoder)
    
    
class CardStatus(Enum):
    ADD = 0
    DELETE = 1
    BURY = 2


class SavedDataDeck(PointerList):
    CARD_STATUS         = "status"               # 0
    CARD_DATA           = "card"                 # 0
    ADDITIONAL_DATA     = "additional"           # 0
    USER_TAGS           = "user_tags"            # 1
    HIERARCHICAL_PREFIX = "hierarchical_prefix"  # 1
    SAVED_IMAGES_PATHS  = "local_images"         # 1
    AUDIO_DATA          = "audio_data"           # 1
    AUDIO_SRCS          = "audio_src"            # 2
    AUDIO_SRCS_TYPE     = "audio_src_type"       # 2
    AUDIO_SAVING_PATHS  = "audio_saving_paths"   # 2

    AUDIO_SRC_TYPE_LOCAL = "local"
    AUDIO_SRC_TYPE_WEB   = "web"

    __slots__ = "_statistics"

    def __init__(self):
        super(SavedDataDeck, self).__init__()
        self._statistics = [0, 0, 0]

    def get_n_added(self):
        return self._statistics[CardStatus.ADD.value]

    def get_n_deleted(self):
        return self._statistics[CardStatus.DELETE.value]

    def get_n_buried(self):
        return self._statistics[CardStatus.BURY.value]

    def append(self, status: CardStatus, card_data: dict[str, Union[str, list[str]]] = None):
        if card_data is None:
            card_data = {}

        res = {SavedDataDeck.CARD_STATUS: status}
        if status != CardStatus.DELETE:
            saving_card = Card(card_data)
            res[SavedDataDeck.CARD_DATA] = saving_card

            additional_data = {}
            if (hierarchical_prefix := card_data.get(SavedDataDeck.HIERARCHICAL_PREFIX)) is not None:
                additional_data[SavedDataDeck.HIERARCHICAL_PREFIX] = hierarchical_prefix

            if (user_tags := card_data.get(SavedDataDeck.USER_TAGS)) is not None:
                additional_data[SavedDataDeck.USER_TAGS] = user_tags

            if (image_data := card_data.get(SavedDataDeck.SAVED_IMAGES_PATHS)) is not None:
                additional_data[SavedDataDeck.SAVED_IMAGES_PATHS] = image_data

            audio_data = {}
            if (audio_src := card_data.get(SavedDataDeck.AUDIO_SRCS)) is not None:
                audio_data[SavedDataDeck.AUDIO_SRCS]          = audio_src
                audio_data[SavedDataDeck.AUDIO_SRCS_TYPE]     = card_data[SavedDataDeck.AUDIO_SRCS_TYPE]
                audio_data[SavedDataDeck.AUDIO_SAVING_PATHS] = card_data[SavedDataDeck.AUDIO_SAVING_PATHS]
            if audio_data:
                additional_data[SavedDataDeck.AUDIO_DATA] = audio_data

            if additional_data:
                res[SavedDataDeck.ADDITIONAL_DATA] = additional_data

        self._data.append(FrozenDict(res))
        self._pointer_position += 1
        self._statistics[status.value] += 1

    def move(self, n: int) -> None:
        if n < 0:
            super(SavedDataDeck, self).move(n)
            for i in range(self.get_pointer_position(), len(self)):
                self._statistics[self[i][SavedDataDeck.CARD_STATUS].value] -= 1
            del self._data[self.get_pointer_position():]
            return
        self._data.extend((FrozenDict({SavedDataDeck.CARD_STATUS: CardStatus.DELETE}) for _ in range(n)))
        self._pointer_position = len(self)
        self._statistics[CardStatus.DELETE.value] += n

    def get_audio_data(self, saving_card_status: CardStatus) -> list[FrozenDict]:
        saving_object = []
        for card_page in self:
            if card_page[SavedDataDeck.CARD_STATUS] != saving_card_status:
                continue
            if (additional := card_page.get(SavedDataDeck.ADDITIONAL_DATA)) is not None and \
                    (audio_data := additional.get(SavedDataDeck.AUDIO_DATA)):
                saving_object.append(audio_data)
        return saving_object

    def get_card_data(self, saving_card_status: CardStatus) -> list[FrozenDict]:
        saving_object = []
        for card_page in self:
            if card_page[SavedDataDeck.CARD_STATUS] != saving_card_status:
                continue
            saving_object.append(card_page[SavedDataDeck.CARD_DATA])
        return saving_object


class SentenceFetcher:
    def __init__(self,
                 sent_fetcher: Callable[[str, int], SentenceGenerator] = lambda *_: [[], True],
                 sentence_batch_size=5):
        self._word: str = ""
        self._sentences: list[str] = []
        self._sentence_fetcher: Callable[[str, int], SentenceGenerator] = sent_fetcher
        self._batch_size: int = sentence_batch_size
        self._sentence_pointer: int = 0
        self._sent_batch_generator: SentenceGenerator = self._get_sent_batch_generator()
        self._local_sentences_flag: bool = True
        self._update_status: bool = False

    def is_local(self):
        return self._local_sentences_flag

    def __call__(self, base_word, base_sentences):
        self._word = base_word
        self._sentences = base_sentences  # REFERENCE!!!
        self._local_sentences_flag = True
        self._sentence_pointer = 0
        self._update_status = False

    def update_word(self, new_word: str):
        if self._word != new_word:
            self._word = new_word
            self._update_status = True

    def _get_sent_batch_generator(self) -> SentenceGenerator:
        """
        Yields: Sentence_batch, error_message
        """
        while True:
            if self._local_sentences_flag:
                self._sentence_pointer = 0
                # Always do the first iteration (not considering update condition)
                while not self._update_status:
                    self._sentence_pointer += self._batch_size
                    yield self._sentences[self._sentence_pointer - self._batch_size:self._sentence_pointer], ""
                    if self._sentence_pointer and self._sentence_pointer >= len(self._sentences):
                        break
                self._local_sentences_flag = False
                # _sentence_fetcher doesn't need update before it's first iteration
                # because of its first argument
                self._update_status = False

            for sentence_batch, error_message in self._sentence_fetcher(self._word, self._batch_size):
                yield sentence_batch, error_message
                if self._update_status:
                    self._update_status = False
                    break
                if self._local_sentences_flag or error_message:
                    break
            else:
                self._local_sentences_flag = True

    def get_sentence_batch(self, word: str) -> tuple[list[str], str, bool]:
        self.update_word(word)
        sentences, error_message = next(self._sent_batch_generator)
        return sentences, error_message, self._local_sentences_flag
