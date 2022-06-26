# errors
error_title = "Ошибка"

# main window
main_window_title_prefix = "Поиск предложений для Anki. Осталось"

# main menu
create_file_menu_label = "Создать"
open_file_menu_label = "Открыть"
save_files_menu_label = "Сохранить"
hotkeys_and_buttons_help_menu_label = "Кнопки/Горячие клавиши"
query_language_menu_label = "Язык запросов"
help_master_menu_label = "Справка"
download_audio_menu_label = "Скачать аудио"
change_media_folder_menu_label = "Сменить пользователя"
file_master_menu_label = "Файл"

add_card_menu_label = "Добавить"
search_inside_deck_menu_label = "Перейти"
statistics_menu_label = "Статистика"
themes_menu_label = "Тема"
language_menu_label = "Язык"
anki_config_menu_label = "Anki"
exit_menu_label = "Выход"

# widgets
browse_button_text = "Найти в браузере"
configure_word_parser_button_text = "Настроить словарь"
find_image_button_normal_text = "Добавить изображение"
find_image_button_image_link_encountered_postfix = "★"
sentence_button_text = "Добавить предложения"
word_text_placeholder = "Слово"
definition_text_placeholder = "Значение"
sentence_text_placeholder_prefix = "Предложение"
skip_button_text = "Skip"
prev_button_text = "Prev"
sound_button_text = "Play"
anki_button_text = "Anki"
bury_button_text = "Bury"
user_tags_field_placeholder = "Тэги"

# choose files
choose_media_dir_message = "Выберете директорию для медиа файлов"
choose_deck_file_message = "Выберете JSON файл со словами"
choose_save_dir_message = "Выберете директорию сохранения"

# create new deck file
create_file_choose_dir_message = "Выберете директорию для файла со словами"
create_file_name_entry_placeholder = "Имя файла"
create_file_name_button_placeholder = "Создать"
create_file_no_file_name_was_given_message = "Не указано имя файла"
create_file_file_already_exists_message = "Файл уже существует.\nВыберите нужную опцию:"
create_file_skip_encounter_button_text = "Пропустить"
create_file_rewrite_encounter_button_text = "Заменить"

# save files
save_files_message = "Файлы сохранены"

# help
buttons_hotkeys_help_message = """
Назначения кнопок:
* 1-5: кнопки выбора соответствующих предложений
* Skip: пропуск карточки
* Prev: возврат к предыдущей карточке
* Bury: откладывает текущую карточку в отдельный файл,
который будет находится в директории сохранения карточек.
Имя этого файла будет такое же, как и у файла с сохраненными карточками +
постфикс _buried

Горячие клавиши (локальные для приложения):
* Ctrl + 0: Перемещает приложение в верхний левый угол экрана
* Ctrl + 1..5: выбор предложения
* Ctrl + d: пропуск карточки
* Ctrl + z: возврат к предыдущей карточке
* Ctrl + q: откладывает текущую карточку в отдельный файл
* Ctrl + Shift + a: вызов окна добавления слова в колоду
* Ctrl + e: вызов окна статистики
* Ctrl + f: вызов окна поиска по колоде

Горячие клавиши (глобальные):
* Ctrl + c + space: добавить выделенного слова в колоду
"""
buttons_hotkeys_help_toplevel_title = "Справка"
word_field_help = "слово (строка)"
alt_terms_field_help = "альтернативные использования (список)"
definition_field_help = "определение (строка)"
sentences_field_help = "предложения (список)"
img_links_field_help = "ссылки на изображения (список)"
audio_links_field_help = "ссылки на аудио (список)"
dict_tags_field_help = "тэги (словарь)"
query_language_docs = """
Унарные операторы:
* логические:
    not

Бинарные операторы:
* логические
    and, or
* арифметические:
    <, <=, >, >=, ==, !=

Ключевые слова:
    in
        Проверяет наличие <thing> в <field>[<subfield_1>][...][<subfield_n>]
        Пример:
            {
                "field": [val_1, .., val_n]}
            }

            thing in field
            Вернет истину если thing находится в [val_1, .., val_n]


Специальные запросы & и команды 
    $ANY
        Возвращает результат текущего уровня иерархии 
        Пример:
            {
                "pos": {
                    "noun": {
                        "data": value_1
                    },
                    "verb" : {
                        "data": value_2
                    }
                }
            }
        $ANY вернет ["noun", "verb"]
        pos[$ANY][data] вернет [value_1, value_2]
        $ANY[$ANY][data] также вернет [value_1, value_2]

    $SELF
        Возвращает ключи текущего уровня иерархии
        Пример:
            {
                "field_1": 1,
                "field_2": 2,
            }
        $SELF вернет [["field_1", "field_2"]]

    d_$
        Конвертирует строку в тип числа.
        По умолчанию, ключи в строке запроса
        (то есть в field[subfield] field и subfield - это ключи)
        обрадатываются как строковый тип. Если у вас ключ с целочисленным или 
        дробным типом, или вам нужно получить элемент массива по конкретному индексу,
        то вам нужен этот префикс.

        Пример:
            {
                "array_field": [1, 2, 3],
                "int_field": {
                    1: [4, 5, 6]
                }
            }

        array_field[d_$1] вернет 2
        int_field[d_$1] вернет [4, 5, 6]

    f_$
        Конвертирует к типу поля
        По умолчанию, "одинокие" числа обрабатываются как числа
        Если ваш ключ - число, то вам понадобится этот префикс

        Пример:
            {
                1: [1, 2, 3],
                2: {
                    "data": [4, 5, 6]
                }
            }

        f_$d_$1 вернет [1, 2, 3]
        Нужно так же использовать d_$ префикс, так как 1 будет считаться полем -> 
        будет обрабатываться как строка
        Обратите внимание:
            Чтобы получить [4, 5, 6] из данной схемы, нужно просто использовать d_$ префикс:
            d_$2[data]

Методы:
    len
        Измеряет длину результата
        Пример:
            {
                "field": [1, 2, 3]
            }
        len(field) вернет 3
        Пример:
            {
                "field": {
                    "subfield_1": {
                        "data": [1, 2, 3]
                    },
                    "subfield_2": {
                        "data": [4, 5]
                    }
                }
            }
        len(field[$ANY][data]) = len([[1, 2, 3], [4, 5]]) = 2

    any
        Вернет истину если хотя бы один элемент истина
        Пример:
            {
                "field": {
                    "subfield_1": {
                        "data": 1
                    },
                    "subfield_2": {
                        "data": 2
                    }
                }
            }
        any(field[$ANY][data] > 1) вернет истину 

    all
        Вернет истину если все элементы - истина
        Пример:
            {
                "field": {
                    "subfield_1": {
                        "data": 1
                    },
                    "subfield_2": {
                        "data": 2
                    }
                }
            }
            all($ANY[$ANY][data] > 0) вернет истину
            all($ANY[$ANY][data] > 1) вернет ложь

    lower
        Конвертирует все строки в нижний регистр, отбросив нестроковые типы
        Пример:
            {
                "field_1": ["ABC", "abc", "AbC", 1],
                "field_2": [["1", "2", "3"]],
                "field_3": "ABC"
            }
        lower(field_1) вернет ["abc", "abc", "abc", ""]
        lower(field_2) вернет [""]
        lower(field_3) вернет "abc"

    upper
        Конвертирует все строки в верхний регистр, отбросив нестроковые типы
        Пример:
            {
                "field_1": ["ABC", "abc", "AbC", 1],
                "field_2": [["1", "2", "3"]],
                "field_3": "abc"
            }
        upper(field_1) вернет ["ABC", "ABC", "ABC", ""]
        upper(field_2) вернет [""]
        upper(field_3) вернет "ABC"

    reduce
        Объединит один(!) слой вложенности:
        Пример:
            {
                "field_1": ["a", "b", "c"],
                "field_2": ["d", "e", "f"]
            }
        $ANY вернет [["a", "b", "c"], ["d", "e", "f"]]
        reduce($ANY) вернет ["a", "b", "c", "d", "e", "f"]
        Обратите внимание:
            {
                "field_1": [["a"], ["b"], ["c"]],
                "field_2": [[["d"], ["e"], ["f"]]]
            }
        $ANY вернет [[["a"], ["b"], ["c"]], [[["d"], ["e"], ["f"]]]]
        reduce($ANY) вернет [["a"], ["b"], ["c"], [["d"], ["e"], ["f"]]]

    Обратите внимание:
        Можно комбинировать методы:
        Пример:
            {
                "field_1": ["ABC", "abc", "AbC"],
                "field_2": ["Def", "dEF", "def"]
            }
        lower(reduce($ANY)) вернет ["abc", "abc", "abc", "def", "def", "def"]

Порядок выполнения:
1) выражения в скобках
2) ключевые слова, методы
3) унарные операторы
4) бинарные операторы
"""
query_language_toplevel_title = "Справка"
general_scheme_label = "Общая схема"
current_scheme_label = "Текущая схема"
query_language_label = "Синтаксис"

# download audio
download_audio_choose_audio_file_title = "Выберете JSON файл c аудио"

# define word
define_word_wrong_regex_message = "Неверно задано регулярное выражение для слова!"
define_word_word_not_found_message = "Слово не найдено!"
define_word_query_language_error_message_title = "Ошибка запроса"

# add_word_dialog
add_word_frame_title = "Добавить"
add_word_entry_placeholder = "Слово"
add_word_additional_filter_entry_placeholder = "Дополнительный фильтр"
add_word_start_parsing_button_text = "Добавить"

# find dialog
find_dialog_empty_query_message = "Пустой запрос!"
find_dialog_wrong_move_message = "Неверно задан переход!"
find_dialog_done_button_text = "Готово"
find_dialog_nothing_found_message = "Ничего не найдено!"
find_dialog_find_frame_title = "Перейти"
find_dialog_find_button_text = "Перейти"

# statistics dialog
statistics_dialog_statistics_window_title = "Статистика"
statistics_dialog_added_label = "Добавлено"
statistics_dialog_buried_label = "Отложено"
statistics_dialog_skipped_label = "Пропущено"
statistics_dialog_cards_left_label = "Осталось"
statistics_dialog_current_file_label = "Файл"
statistics_dialog_saving_dir_label = "Директория сохранения"
statistics_dialog_media_dir_label = "Медиа"

# anki dialog
anki_dialog_anki_toplevel_title = "Настройки Anki"
anki_dialog_anki_deck_entry_placeholder = "Колода поиска"
anki_dialog_anki_field_entry_placeholder = "Поле поиска"
anki_dialog_save_anki_settings_button_text = "Сохранить"

# theme change
restart_app_text = "Изменения вступят в силу после перезагрузки приложения!"

# program exit
on_closing_message_title = "Выход"
on_closing_message = "Вы точно хотите выйти?"

# configure_dictionary
configure_dictionary_dict_label_text = "Словарь"
configure_dictionary_audio_getter_label_text = "Получение аудио"
configure_dictionary_card_processor_label_text = "Формат карточки"
configure_dictionary_format_processor_label_text = "Формат итогового файла"

# play_sound
play_sound_playsound_toplevel_title = "Аудио"
play_sound_local_audio_not_found_message = "Локальный файл не найден"
play_sound_no_audio_source_found_message = "Не откуда брать аудио"

# request anki
request_anki_connection_error_message = "Проверьте аддон AnkiConnect и откройте Anki"
request_anki_general_request_error_message_prefix = "Результат ошибки"
