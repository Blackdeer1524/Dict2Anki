# Dict2Anki
Sentence-mining app written in python using Tkinter.

## Quickly create card
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/choose_sentence.gif)

## Add word
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/add_word.gif)

## Add sentences from external sources
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/add_sentences.gif)

## Download images from web
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/img.gif)

## Download audio
* Menu option
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/audio.gif)

* On closing
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/audio_on_closing.gif)

## Browse anki
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/anki_search.gif)

## Use web browser
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/browser.gif)

## Bury card to watch them later
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/bury_and_reopen.gif)

## Search in already created decks
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/find_word.gif)

## Skip redundant cards
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/move.gif)

## Use query language to find what you realy need
* when adding new card

![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/query_language.gif)

* when looking through created deck

![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/query_language_find.gif)

## View session statistics
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/statistics.gif)

## Change themes
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/themes.gif)

## Multiple languages support
![](https://github.com/Blackdeer1524/Dict2Anki/blob/main/app_demonstration/language_packs.gif)

# Requirements
* Python 3.10+
* Libraries from corresponding requirements.txt files 

# Card format
Standard card fields:
  * word
  * alt_terms
  * definition
  * examples
  * image_links
  * audio_links
  * tags

These fields are used to display information about current card.
Card fields can be extended, but new fields will not be desplayed.
The main purpose of field extension is to use these new fields inside
format savers.

# Plugins
To view every plugin interface, see ./plugins_management/interfaces.py

## Word parsers
### Local word parsers
Parses local JSON dictionary
**Dictionary format**:
{[<word>[str], <data>[dict]], ...}
you will have to put this dictionary into ./media folder

To register a local dictionary, create a python file inside **./plugins/parsers/word_parsers/local/** with the following protocol:
  * DICTIONARY_PATH: str - relative path to the JSON dictionary that is located inside ./media folder
  * SCHEME_DOCS: str - documentation to the resulting scheme
  * translate(word: str, word_dict: dict) function that converts [<word>, <data>] format to Card format

### Web word parsers  
To create a web parser, create a python file inside **./plugins/parsers/word_parsers/web/** with the following protocol:
  * SCHEME_DOCS: str - documentation to the resulting scheme
  * define(word: str) function that returns **dictionary format**
  * translate(word: str, word_dict: dict) function that converts [<word>, <data>] format to **Card format**

## Sentence parsers
To create a sentence parser, create a python file inside **./plugins/parsers/sentence_parsers/** with the following protocol:
  * get_sentence_batch(word: str, size: int) -> Iterator[tuple[list[str], str]] function that takes word to which sentences 
  are needed and size of batch of sentences that will be returned on every iteration. This function has to yield batch of sentences
  allong with error message ("" empty string if no errors occured)

## Image parsers
To create an image parser, create a python file inside **./plugins/parsers/image_parsers/** with the following protocol:
  * get_image_links(word: str) -> Generator[tuple[list[str], str], int, tuple[list[str], str]] function that takes word for which
  images are needed. This function has to have 2 stages
    * initialization on first next() call
    * current step batch size initialization on <gen>.send(batch_size) that returns batch_size image links 
 
## Local audio getters
To register folder with audio files,, create a python file inside **./plugins/parsers/local_audio_getters/** with the following protocol:
  * AUDIO_FOLDER: str - relative path to the folder with audio files that is located inside ./media folder
  * get_local_audios(word: str, dict_tags: dict) -> list[str] function that takes word to whick audio is needed and dict_tags for the additional info
  and returns a list of paths.

# Saving
## Card processors
You may want to create special card processors to other applications from Anki. These apps may have special requirements for card format. For
Example, to add an audio file to anki, one has to wrap its file name in [sound:<filename>].
To create a card processor, create a python file inside **./plugins/saving/card_processors/** with the following protocol:
  * get_save_image_name(word: str, image_source: str, image_parser_name: str, dict_tags: dict) -> str function that returns saving image file name
  * get_card_image_name(saved_image_path: str) -> str function that returns wrapped saved_image_path (this path is *absolute*)
  * get_save_audio_name(word: str, audio_provider: str, multiple_postfix: str, dict_tags: dict) -> str function that returns saving audio file name
  * get_card_audio_name(saved_audio_path: str) -> str function that returns wrapped saved_audio_path (this path is *absolute*)
  * process_card(card: dict) -> None function that processes card in-place

## Format processors
Transforms saved card collection to needed file format
To create a format processor, create a python file inside **./plugins/saving/format_processors/** with the following protocol:
  * save(deck: SavedDataDeck,
         saving_card_status: CardStatus,
         saving_path: str,
         image_names_wrapper: Callable[[str], str],
         audio_names_wrapper: Callable[[str], str]) -> None function that iterates through SavedDataDeck (located in ./utils/cards.py) and 
    pickes cards with saving_card_status from which the format is formed. image_names_wrapper and audio_names_wrapper are wrappers from current 
    card processor

# Themes
To create a theme, create a python file inside **./plugins/themes/** with the following protocol:
  * label_cfg: dict - Tkinter Label widget config, compatable with Text widget
  * button_cfg: dict - Tkinter Button widget config
  * text_cfg: dict - Tkinter Text widget config
  * entry_cfg: dict - Tkinter Entry widget config
  * checkbutton_cfg: dict - Tkinter Checkbutton widget config
  * toplevel_cfg: dict - Tkinter Toplevel widget config
  * root_cfg: dict - Tkinter Tk config
  * frame_cfg: dict - Tkinter Frame widget config
  * option_menu_cfg: dict - Tkinter OptionMenu widget config
  * option_submenus_cfg: dict - config used to configure submenus of OptionMenu

# Language packages
To create a language package, create a python file inside **./plugins/language_packages/** with the protocol listed inside 
  ./plugins_management/interfaces.LanguagePackageInterface class
 
