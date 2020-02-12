from text_tools.parse import parse

langs = [
    "cz.txt",
    "da.txt",
    "de.txt",
    "en.txt",
    "es.txt",
    "fi.txt",
    "fr.txt",
    "it.txt",
    "nl.txt",
    "pl.txt",
    "ru.txt",
    "sv.txt",
]


def check_all_langs():
    for lang in langs:
        lang = "j:/projects/freeorion/default/stringtables/" + lang
        print(f"Check {lang}")
        try:
            parse(lang)
        except Exception as e:
            print(e)


check_all_langs()
