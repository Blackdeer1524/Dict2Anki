from dataclasses import dataclass
from typing import Callable

from app_utils.cards import CardStatus
from app_utils.cards import SavedDataDeck
from plugins_loading.interfaces import CardProcessorInterface
from plugins_loading.interfaces import DeckSavingFormatInterface
from plugins_loading.interfaces import ImageParserInterface
from plugins_loading.interfaces import LanguagePackageInterface
from plugins_loading.interfaces import LocalAudioGetterInterface
from plugins_loading.interfaces import WebAudioGetterInterface
from plugins_loading.interfaces import LocalWordParserInterface
from plugins_loading.interfaces import ThemeInterface
from plugins_loading.interfaces import WebSentenceParserInterface
from plugins_loading.interfaces import WebWordParserInterface
from plugins_management.config_management import LoadableConfig
from plugins_management.parsers_return_types import SentenceGenerator, ImageGenerator


@dataclass(init=False, repr=False, frozen=True, eq=False, order=False)
class _PluginContainer:
    name: str
    
    def __init__(self, name: str):
        object.__setattr__(self, "name", name)


class LanguagePackageContainer(_PluginContainer, LanguagePackageInterface):
    def __init__(self, name: str, source_module: LanguagePackageInterface):
        super(LanguagePackageContainer, self).__init__(name)
        # errors
        object.__setattr__(self, "error_title", source_module.error_title)

        # main window
        object.__setattr__(self, "main_window_title_prefix", source_module.main_window_title_prefix)

        # main menu
        object.__setattr__(self, "create_file_menu_label", source_module.create_file_menu_label)
        object.__setattr__(self, "open_file_menu_label", source_module.open_file_menu_label)
        object.__setattr__(self, "save_files_menu_label", source_module.save_files_menu_label)
        object.__setattr__(self, "hotkeys_and_buttons_help_menu_label",
                           source_module.hotkeys_and_buttons_help_menu_label)
        object.__setattr__(self, "query_language_menu_label", source_module.query_language_menu_label)
        object.__setattr__(self, "help_master_menu_label", source_module.help_master_menu_label)
        object.__setattr__(self, "download_audio_menu_label", source_module.download_audio_menu_label)
        object.__setattr__(self, "change_media_folder_menu_label", source_module.change_media_folder_menu_label)
        object.__setattr__(self, "file_master_menu_label", source_module.file_master_menu_label)

        object.__setattr__(self, "add_card_menu_label", source_module.add_card_menu_label)
        object.__setattr__(self, "search_inside_deck_menu_label", source_module.search_inside_deck_menu_label)
        object.__setattr__(self, "statistics_menu_label", source_module.statistics_menu_label)
        object.__setattr__(self, "themes_menu_label", source_module.themes_menu_label)
        object.__setattr__(self, "language_menu_label", source_module.language_menu_label)
        object.__setattr__(self, "anki_config_menu_label", source_module.anki_config_menu_label)
        object.__setattr__(self, "exit_menu_label", source_module.exit_menu_label)

        # widgets
        object.__setattr__(self, "browse_button_text", source_module.browse_button_text)
        object.__setattr__(self, "configure_word_parser_button_text",
                           source_module.configure_word_parser_button_text)
        object.__setattr__(self, "find_image_button_normal_text", source_module.find_image_button_normal_text)
        object.__setattr__(self, "find_image_button_image_link_encountered_postfix",
                           source_module.find_image_button_image_link_encountered_postfix)
        object.__setattr__(self, "sentence_button_text", source_module.sentence_button_text)
        object.__setattr__(self, "word_text_placeholder", source_module.word_text_placeholder)
        object.__setattr__(self, "definition_text_placeholder", source_module.definition_text_placeholder)
        object.__setattr__(self, "sentence_text_placeholder_prefix", source_module.sentence_text_placeholder_prefix)
        object.__setattr__(self, "skip_button_text", source_module.skip_button_text)
        object.__setattr__(self, "prev_button_text", source_module.prev_button_text)
        object.__setattr__(self, "sound_button_text", source_module.sound_button_text)
        object.__setattr__(self, "anki_button_text", source_module.anki_button_text)
        object.__setattr__(self, "bury_button_text", source_module.bury_button_text)
        object.__setattr__(self, "user_tags_field_placeholder", source_module.user_tags_field_placeholder)

        # choose files
        object.__setattr__(self, "choose_media_dir_message", source_module.choose_media_dir_message)
        object.__setattr__(self, "choose_deck_file_message", source_module.choose_deck_file_message)
        object.__setattr__(self, "choose_save_dir_message", source_module.choose_save_dir_message)

        # create new deck file
        object.__setattr__(self, "create_file_choose_dir_message", source_module.create_file_choose_dir_message)
        object.__setattr__(self, "create_file_name_entry_placeholder", source_module.create_file_name_entry_placeholder)
        object.__setattr__(self, "create_file_name_button_placeholder",
                           source_module.create_file_name_button_placeholder)
        object.__setattr__(self, "create_file_no_file_name_was_given_message",
                           source_module.create_file_no_file_name_was_given_message)
        object.__setattr__(self, "create_file_file_already_exists_message",
                           source_module.create_file_file_already_exists_message)
        object.__setattr__(self, "create_file_skip_encounter_button_text",
                           source_module.create_file_skip_encounter_button_text)
        object.__setattr__(self, "create_file_rewrite_encounter_button_text",
                           source_module.create_file_rewrite_encounter_button_text)

        # save files
        object.__setattr__(self, "save_files_message", source_module.save_files_message)

        # help
        object.__setattr__(self, "buttons_hotkeys_help_message", source_module.buttons_hotkeys_help_message)
        object.__setattr__(self, "buttons_hotkeys_help_toplevel_title",
                           source_module.buttons_hotkeys_help_toplevel_title)
        object.__setattr__(self, "word_field_help", source_module.word_field_help)
        object.__setattr__(self, "alt_terms_field_help", source_module.special_field_help)
        object.__setattr__(self, "definition_field_help", source_module.definition_field_help)
        object.__setattr__(self, "sentences_field_help", source_module.sentences_field_help)
        object.__setattr__(self, "img_links_field_help", source_module.img_links_field_help)
        object.__setattr__(self, "audio_links_field_help", source_module.audio_links_field_help)
        object.__setattr__(self, "dict_tags_field_help", source_module.dict_tags_field_help)
        object.__setattr__(self, "query_language_docs", source_module.query_language_docs)
        object.__setattr__(self, "query_language_toplevel_title", source_module.query_language_toplevel_title)
        object.__setattr__(self, "general_scheme_label", source_module.general_scheme_label)
        object.__setattr__(self, "current_scheme_label", source_module.current_scheme_label)
        object.__setattr__(self, "query_language_label", source_module.query_language_label)

        # download audio
        object.__setattr__(self, "download_audio_choose_audio_file_title",
                           source_module.download_audio_choose_audio_file_title)

        # define word
        object.__setattr__(self, "define_word_wrong_regex_message", source_module.define_word_wrong_regex_message)
        object.__setattr__(self, "define_word_word_not_found_message", source_module.define_word_word_not_found_message)
        object.__setattr__(self, "define_word_query_language_error_message_title",
                           source_module.define_word_query_language_error_message_title)

        # add_word_dialog
        object.__setattr__(self, "add_word_frame_title", source_module.add_word_frame_title)
        object.__setattr__(self, "add_word_entry_placeholder", source_module.add_word_entry_placeholder)
        object.__setattr__(self, "add_word_additional_filter_entry_placeholder",
                           source_module.add_word_additional_filter_entry_placeholder)
        object.__setattr__(self, "add_word_start_parsing_button_text", source_module.add_word_start_parsing_button_text)

        # find dialog
        object.__setattr__(self, "find_dialog_empty_query_message", source_module.find_dialog_empty_query_message)
        object.__setattr__(self, "find_dialog_wrong_move_message", source_module.find_dialog_wrong_move_message)
        object.__setattr__(self, "find_dialog_done_button_text", source_module.find_dialog_done_button_text)
        object.__setattr__(self, "find_dialog_nothing_found_message", source_module.find_dialog_nothing_found_message)
        object.__setattr__(self, "find_dialog_find_frame_title", source_module.find_dialog_find_frame_title)
        object.__setattr__(self, "find_dialog_find_button_text", source_module.find_dialog_find_button_text)

        # statistics dialog
        object.__setattr__(self, "statistics_dialog_statistics_window_title",
                           source_module.statistics_dialog_statistics_window_title)
        object.__setattr__(self, "statistics_dialog_added_label", source_module.statistics_dialog_added_label)
        object.__setattr__(self, "statistics_dialog_buried_label", source_module.statistics_dialog_buried_label)
        object.__setattr__(self, "statistics_dialog_skipped_label", source_module.statistics_dialog_skipped_label)
        object.__setattr__(self, "statistics_dialog_cards_left_label", source_module.statistics_dialog_cards_left_label)
        object.__setattr__(self, "statistics_dialog_current_file_label",
                           source_module.statistics_dialog_current_file_label)
        object.__setattr__(self, "statistics_dialog_saving_dir_label", source_module.statistics_dialog_saving_dir_label)
        object.__setattr__(self, "statistics_dialog_media_dir_label", source_module.statistics_dialog_media_dir_label)

        # anki dialog
        object.__setattr__(self, "anki_dialog_anki_toplevel_title", source_module.anki_dialog_anki_toplevel_title)
        object.__setattr__(self, "anki_dialog_anki_deck_entry_placeholder",
                           source_module.anki_dialog_anki_deck_entry_placeholder)
        object.__setattr__(self, "anki_dialog_anki_field_entry_placeholder",
                           source_module.anki_dialog_anki_field_entry_placeholder)
        object.__setattr__(self, "anki_dialog_save_anki_settings_button_text",
                           source_module.anki_dialog_save_anki_settings_button_text)

        # theme change
        object.__setattr__(self, "restart_app_text", source_module.restart_app_text)

        # program exit
        object.__setattr__(self, "on_closing_message_title", source_module.on_closing_message_title)
        object.__setattr__(self, "on_closing_message", source_module.on_closing_message)

        # configure_dictionary
        object.__setattr__(self, "configure_dictionary_dict_label_text",
                           source_module.configure_dictionary_dict_label_text)
        object.__setattr__(self, "configure_dictionary_audio_getter_label_text",
                           source_module.configure_dictionary_audio_getter_label_text)
        object.__setattr__(self, "configure_dictionary_card_processor_label_text",
                           source_module.configure_dictionary_card_processor_label_text)
        object.__setattr__(self, "configure_dictionary_format_processor_label_text",
                           source_module.configure_dictionary_format_processor_label_text)

        object.__setattr__(self, "configuration_window_conf_window_title",
                           source_module.configuration_window_conf_window_title)
        object.__setattr__(self, "configuration_window_restore_defaults_done_message",
                           source_module.configuration_window_restore_defaults_done_message)
        object.__setattr__(self, "configuration_window_restore_defaults_button_text",
                           source_module.configuration_window_restore_defaults_button_text)
        object.__setattr__(self, "configuration_window_cancel_button_text",
                           source_module.configuration_window_cancel_button_text)
        object.__setattr__(self, "configuration_window_bad_json_scheme_message",
                           source_module.configuration_window_bad_json_scheme_message)
        object.__setattr__(self, "configuration_window_saved_message",
                           source_module.configuration_window_saved_message)
        object.__setattr__(self, "configuration_window_wrong_type_field",
                           source_module.configuration_window_wrong_type_field)
        object.__setattr__(self, "configuration_window_wrong_value_field",
                           source_module.configuration_window_wrong_value_field)
        object.__setattr__(self, "configuration_window_missing_keys_field",
                           source_module.configuration_window_missing_keys_field)
        object.__setattr__(self, "configuration_window_unknown_keys_field",
                           source_module.configuration_window_unknown_keys_field)
        object.__setattr__(self, "configuration_window_expected_prefix",
                           source_module.configuration_window_expected_prefix)
        object.__setattr__(self, "configuration_window_done_button_text",
                           source_module.configuration_window_done_button_text)

        # play_sound
        object.__setattr__(self, "play_sound_playsound_toplevel_title",
                           source_module.play_sound_playsound_toplevel_title)
        object.__setattr__(self, "play_sound_local_audio_not_found_message",
                           source_module.play_sound_local_audio_not_found_message)
        object.__setattr__(self, "play_sound_no_audio_source_found_message",
                           source_module.play_sound_no_audio_source_found_message)

        # request anki
        object.__setattr__(self, "request_anki_connection_error_message",
                           source_module.request_anki_connection_error_message)
        object.__setattr__(self, "request_anki_general_request_error_message_prefix",
                           source_module.request_anki_general_request_error_message_prefix)

        # audio downloader
        object.__setattr__(self, "audio_downloader_title",
                           source_module.audio_downloader_title)
        object.__setattr__(self, "audio_downloader_file_exists_message",
                           source_module.audio_downloader_file_exists_message)
        object.__setattr__(self, "audio_downloader_skip_encounter_button_text",
                           source_module.audio_downloader_skip_encounter_button_text)
        object.__setattr__(self, "audio_downloader_rewrite_encounter_button_text",
                           source_module.audio_downloader_rewrite_encounter_button_text)
        object.__setattr__(self, "audio_downloader_apply_to_all_button_text",
                           source_module.audio_downloader_apply_to_all_button_text)
        object.__setattr__(self, "audio_downloader_n_errors_message_prefix",
                           source_module.audio_downloader_n_errors_message_prefix)

        # image downloader
        object.__setattr__(self, "image_search_title",
                           source_module.image_search_title)
        object.__setattr__(self, "image_search_start_search_button_text",
                           source_module.image_search_start_search_button_text)
        object.__setattr__(self, "image_search_show_more_button_text",
                           source_module.image_search_show_more_button_text)
        object.__setattr__(self, "image_search_save_button_text",
                           source_module.image_search_save_button_text)
        object.__setattr__(self, "image_search_empty_search_query_message",
                           source_module.image_search_empty_search_query_message)


class ThemeContainer(_PluginContainer, ThemeInterface):
    def __init__(self, name: str, source_module: ThemeInterface):
        super(ThemeContainer, self).__init__(name)
        object.__setattr__(self, "label_cfg",           source_module.label_cfg)
        object.__setattr__(self, "button_cfg",          source_module.button_cfg)
        object.__setattr__(self, "text_cfg",            source_module.text_cfg)
        object.__setattr__(self, "entry_cfg",           source_module.entry_cfg)
        object.__setattr__(self, "checkbutton_cfg",     source_module.checkbutton_cfg)
        object.__setattr__(self, "toplevel_cfg",        source_module.toplevel_cfg)
        object.__setattr__(self, "root_cfg",            source_module.root_cfg)
        object.__setattr__(self, "frame_cfg",           source_module.frame_cfg)
        object.__setattr__(self, "option_menu_cfg",     source_module.option_menu_cfg)
        object.__setattr__(self, "option_submenus_cfg", source_module.option_submenus_cfg)


class WebWordParserContainer(_PluginContainer):
    scheme_docs: str
    config: LoadableConfig
    define: Callable[[str], list[(str, dict)]]
    translate: Callable[[str, dict], dict]

    def __init__(self, name: str, source_module: WebWordParserInterface):
        super(WebWordParserContainer, self).__init__(name)
        object.__setattr__(self, "scheme_docs", source_module.SCHEME_DOCS)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "define", source_module.define)
        object.__setattr__(self, "translate", source_module.translate)


class LocalWordParserContainer(_PluginContainer):
    scheme_docs: str
    config: LoadableConfig
    local_dict_name: str
    translate: Callable[[str], dict]

    def __init__(self, name: str, source_module: LocalWordParserInterface):
        super(LocalWordParserContainer, self).__init__(name)
        object.__setattr__(self, "scheme_docs", source_module.SCHEME_DOCS)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "local_dict_name", source_module.DICTIONARY_PATH)
        object.__setattr__(self, "translate", source_module.translate)


class WebSentenceParserContainer(_PluginContainer):
    config: LoadableConfig
    get_sentence_batch: Callable[[str, int], SentenceGenerator]

    def __init__(self, name: str, source_module: WebSentenceParserInterface):
        super(WebSentenceParserContainer, self).__init__(name)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "get_sentence_batch", source_module.get_sentence_batch)


class ImageParserContainer(_PluginContainer):
    config: LoadableConfig
    get_image_links: Callable[[str], ImageGenerator]

    def __init__(self, name: str, source_module: ImageParserInterface):
        super(ImageParserContainer, self).__init__(name)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "get_image_links", source_module.get_image_links)


class CardProcessorContainer(_PluginContainer):
    get_save_image_name: Callable[[str, str, dict], str]
    get_card_image_name: Callable[[str], str]
    get_save_audio_name: Callable[[str, str, str, dict], str]
    get_card_audio_name: Callable[[str], str]
    process_card:        Callable[[dict], None]

    def __init__(self, name: str, source_module: CardProcessorInterface):
        super(CardProcessorContainer, self).__init__(name)
        object.__setattr__(self, "get_save_image_name", source_module.get_save_image_name)
        object.__setattr__(self, "get_card_image_name", source_module.get_card_image_name)
        object.__setattr__(self, "get_save_audio_name", source_module.get_save_audio_name)
        object.__setattr__(self, "get_card_audio_name", source_module.get_card_audio_name)
        object.__setattr__(self, "process_card",        source_module.process_card)


class DeckSavingFormatContainer(_PluginContainer):
    save: Callable[[SavedDataDeck, CardStatus, str, Callable[[str], str], Callable[[str], str]], None]

    def __init__(self, name: str, source_module: DeckSavingFormatInterface):
        super(DeckSavingFormatContainer, self).__init__(name)
        object.__setattr__(self, "save", source_module.save)


class LocalAudioGetterContainer(_PluginContainer):
    config: LoadableConfig
    get_local_audios: Callable[[str, dict], str]

    def __init__(self, name: str, source_module: LocalAudioGetterInterface):
        super(LocalAudioGetterContainer, self).__init__(name)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "get_local_audios", source_module.get_local_audios)


class WebAudioGetterContainer(_PluginContainer):
    config: LoadableConfig
    get_local_audios: Callable[[str, dict], str]

    def __init__(self, name: str, source_module: WebAudioGetterInterface):
        super(WebAudioGetterContainer, self).__init__(name)
        object.__setattr__(self, "config", source_module.config)
        object.__setattr__(self, "get_web_audios", source_module.get_web_audios)
