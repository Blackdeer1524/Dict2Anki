import json
from typing import Callable

from utils.cards import SavedDataDeck, CardStatus
from utils.storages import FrozenDictJSONEncoder


def save(deck: SavedDataDeck,
         saving_card_status: CardStatus,
         saving_path: str,
         image_names_wrapper: Callable[[str], str],
         audio_names_wrapper: Callable[[str], str]):
    saving_object = deck.get_audio_data(saving_card_status)

    if saving_object:
        with open(saving_path + ".json", "w", encoding="utf-8") as deck_file:
            json.dump(saving_object, deck_file, cls=FrozenDictJSONEncoder)
