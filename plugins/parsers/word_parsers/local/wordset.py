DICTIONARY_PATH = "wordset"


def translate(word: str, word_dict: dict):
    word_list = []
    for pos in word_dict:
        # uk_ipa = word_dict[word][pos]["UK IPA"]
        # us_ipa = word_dict[word][pos]["US IPA"]
        for name in ("examples", "domain", "labels_and_codes", "level", "region", "usage"):
            if word_dict[pos].get(name) is None:
                word_dict[pos][name] = []
            while len(word_dict[pos]["definitions"]) > len(word_dict[pos][name]):
                word_dict[pos][name].append([""])

        for definition, examples, domain, labels_and_codes, level, \
            region, usage in zip(word_dict[pos]["definitions"],
                                 word_dict[pos]["examples"],
                                 word_dict[pos]["domain"],
                                 word_dict[pos]["labels_and_codes"],
                                 word_dict[pos]["level"],
                                 word_dict[pos]["region"],
                                 word_dict[pos]["usage"]):

            # {"word": слово_n, "meaning": значение_n, "Sen_Ex": [пример_1, ..., пример_n]}
            word_list.append({"word": word, "meaning": definition,
                              "Sen_Ex": examples, "domain": domain, "level": level, "region": region,
                              "usage": usage, "pos": pos})
    return word_list
