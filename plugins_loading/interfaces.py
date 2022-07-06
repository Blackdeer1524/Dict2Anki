from typing import Protocol, Callable

from plugins_management.parsers_return_types import SentenceGenerator, ImageGenerator
from plugins_management.config_management import LoadableConfig
from app_utils.cards import SavedDataDeck, CardStatus


class LanguagePackageInterface(Protocol):
    # errors
    error_title: str

    # main window
    main_window_title_prefix: str

    # main menu
    create_file_menu_label: str
    open_file_menu_label: str
    save_files_menu_label: str
    hotkeys_and_buttons_help_menu_label: str
    query_language_menu_label: str
    help_master_menu_label: str
    download_audio_menu_label: str
    change_media_folder_menu_label: str
    file_master_menu_label: str

    add_card_menu_label: str
    search_inside_deck_menu_label: str
    statistics_menu_label: str
    themes_menu_label: str
    language_menu_label: str
    anki_config_menu_label: str
    exit_menu_label: str

    # widgets
    browse_button_text: str
    configure_word_parser_button_text: str
    find_image_button_normal_text: str
    find_image_button_image_link_encountered_postfix: str
    sentence_button_text: str
    word_text_placeholder: str
    definition_text_placeholder: str
    sentence_text_placeholder_prefix: str
    skip_button_text: str
    prev_button_text: str
    sound_button_text: str
    anki_button_text: str
    bury_button_text: str
    user_tags_field_placeholder: str

    # choose files
    choose_media_dir_message: str
    choose_deck_file_message: str
    choose_save_dir_message: str

    # create new deck file
    create_file_choose_dir_message: str
    create_file_name_entry_placeholder: str
    create_file_name_button_placeholder: str
    create_file_no_file_name_was_given_message: str
    create_file_file_already_exists_message: str
    create_file_skip_encounter_button_text: str
    create_file_rewrite_encounter_button_text: str

    # save files
    save_files_message: str

    # help
    buttons_hotkeys_help_message: str
    buttons_hotkeys_help_toplevel_title: str
    word_field_help: str
    special_field_help: str
    definition_field_help: str
    sentences_field_help: str
    img_links_field_help: str
    audio_links_field_help: str
    dict_tags_field_help: str
    query_language_docs: str
    query_language_toplevel_title: str
    general_scheme_label: str
    current_scheme_label: str
    query_language_label: str

    # download audio
    download_audio_choose_audio_file_title: str

    # define word
    define_word_wrong_regex_message: str
    define_word_word_not_found_message: str
    define_word_query_language_error_message_title: str

    # add_word_dialog
    add_word_frame_title: str
    add_word_entry_placeholder: str
    add_word_additional_filter_entry_placeholder: str
    add_word_start_parsing_button_text: str

    # find dialog
    find_dialog_empty_query_message: str
    find_dialog_wrong_move_message: str
    find_dialog_done_button_text: str
    find_dialog_nothing_found_message: str
    find_dialog_find_frame_title: str
    find_dialog_find_button_text: str

    # statistics dialog
    statistics_dialog_statistics_window_title: str
    statistics_dialog_added_label: str
    statistics_dialog_buried_label: str
    statistics_dialog_skipped_label: str
    statistics_dialog_cards_left_label: str
    statistics_dialog_current_file_label: str
    statistics_dialog_saving_dir_label: str
    statistics_dialog_media_dir_label: str

    # anki dialog
    anki_dialog_anki_toplevel_title: str
    anki_dialog_anki_deck_entry_placeholder: str
    anki_dialog_anki_field_entry_placeholder: str
    anki_dialog_save_anki_settings_button_text: str

    # theme change
    restart_app_text: str

    # program exit
    on_closing_message_title: str
    on_closing_message: str

    # configure_dictionary
    configure_dictionary_dict_label_text: str
    configure_dictionary_audio_getter_label_text: str
    configure_dictionary_card_processor_label_text: str
    configure_dictionary_format_processor_label_text: str

    # call_configuration_window
    configuration_window_conf_window_title: str
    configuration_window_restore_defaults_done_message: str
    configuration_window_restore_defaults_button_text: str
    configuration_window_cancel_button_text: str
    configuration_window_bad_json_scheme_message: str
    configuration_window_saved_message: str
    configuration_window_wrong_type_field: str
    configuration_window_wrong_value_field: str
    configuration_window_missing_keys_field: str
    configuration_window_unknown_keys_field: str
    configuration_window_expected_prefix: str
    configuration_window_done_button_text: str

    # play_sound
    play_sound_playsound_toplevel_title: str
    play_sound_local_audio_not_found_message: str
    play_sound_no_audio_source_found_message: str

    # request anki
    request_anki_connection_error_message: str
    request_anki_general_request_error_message_prefix: str

    # audio downloader
    audio_downloader_title: str
    audio_downloader_file_exists_message: str
    audio_downloader_skip_encounter_button_text: str
    audio_downloader_rewrite_encounter_button_text: str
    audio_downloader_apply_to_all_button_text: str
    audio_downloader_n_errors_message_prefix: str

    # image downloader
    image_search_title: str
    image_search_start_search_button_text: str
    image_search_show_more_button_text: str
    image_search_save_button_text: str
    image_search_empty_search_query_message: str


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
    SCHEME_DOCS: str
    config: LoadableConfig

    @staticmethod
    def define(word: str) -> dict:
        ...

    @staticmethod
    def translate(word: str, word_dict: dict) -> dict:
        ...


class LocalWordParserInterface(Protocol):
    SCHEME_DOCS: str
    config: LoadableConfig
    DICTIONARY_PATH: str

    @staticmethod
    def translate(word: str, word_dict: dict) -> dict:
        ...


class WebSentenceParserInterface(Protocol):
    config: LoadableConfig

    @staticmethod
    def get_sentence_batch(word: str, size: int) -> SentenceGenerator:
        ...


class ImageParserInterface(Protocol):
    config: LoadableConfig

    @staticmethod
    def get_image_links(word: str) -> ImageGenerator:
        ...


class CardProcessorInterface(Protocol):
    @staticmethod
    def get_save_image_name(word: str,
                            image_source: str,
                            image_parser_name: str,
                            dict_tags: dict) -> str:
        ...

    @staticmethod
    def get_card_image_name(saved_image_path: str) -> str:
        ...

    @staticmethod
    def get_save_audio_name(word: str,
                            audio_provider: str,
                            multiple_postfix: str,
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
    def save(deck: SavedDataDeck,
             saving_card_status: CardStatus,
             saving_path: str,
             image_names_wrapper: Callable[[str], str],
             audio_names_wrapper: Callable[[str], str]):
        ...


class LocalAudioGetterInterface(Protocol):
    config: LoadableConfig
    AUDIO_FOLDER: str

    @staticmethod
    def get_local_audios(word: str, dict_tags: dict) -> list[str]:
        ...


class WebAudioGetterInterface(Protocol):
    config: LoadableConfig

    @staticmethod
    def get_web_audios(word: str, dict_tags: dict) -> tuple[tuple[list[str], list[str]], str]:
        """returns ((<audio urls>, <additional information>), <error_message>)"""
        ...
