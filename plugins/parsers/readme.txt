image_parsers
    - parser_name.py
        * required function name: get_image_links
            ~ list of image links (jpg | png)

media
    # Folder for local dictionaries and local audio files
    dictionaries have to be sorted by words!
    * local_dict.json
        ~ [
            (word_n, result_1),
            ...,
            (word_n, result_n)
          ]

word_parsers
    - local_parser_name.py
	    * required function name: translate
            	~ translates result obtained from json dict into appropriate format*
        * required constant in file: DICTIONARY_PATH="path to local json dict, that is placed in media folder"
    - web_parser_name.py
        * required function name: define
            ~ returns search result of appropriate format'

sentence_parsers
    - web_parser_name.py
        * required function name: get_sentence_batch
            ~ generator that yields lists of sentences

=======================================================================================
appropriate format:
[{
  "word": word_1, 
  "meaning": definition_1,
  "Sen_Ex": examples_1, 
  "domain": domain_1, 
  "level": level_1, 
  "region": region_1,
  "usage": usage_1, 
  "pos": pos_1
},
...
{
  "word": word_N, 
  "meaning": definition_N,
  "Sen_Ex": examples_N, 
  "domain": domain_N, 
  "level": level_N, 
  "region": region_N,
  "usage": usage_N, 
  "pos": pos_N
}]

Mandatory fields:
    word, meaning, Sen_Ex
Optional fields:
    domain, level, region, usage, pos