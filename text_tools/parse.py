import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Dict

KEY_ALLOWED_SYMBOLS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")

tag = re.compile("\[\[([a-z]+ )?(.+?)\]\]")
EN = "en.txt"


class InvalidKey(Exception):
    ...


class UnknownReference(Exception):
    ...


class UnusedKey(Exception):
    ...


@dataclass
class Item:
    key: str
    value: str
    pre_comment: tuple
    comment: str

    def is_translated(self):
        return self.comment.strip() == "translated" if self.comment else False

    def get_key_display(self):
        comment = self.comment.strip() if self.comment else False
        if not comment:
            comment_part = ''
        else:
            comment_part = f" # {comment}"
        pre_comment_part = '\n'.join(self.pre_comment) + '\n' if self.pre_comment else ''
        return f"{pre_comment_part}{self.key}{comment_part}"


def value_for_string_table(value: str) -> str:
    """
    Return value how it should looks in *.txt file.
    """
    if value.startswith("'''") and value.endswith("'''"):
        value = value[3:-3]

    if "\n" in value or value.startswith((" ", "\t")) or value.endswith((" ", "\t")):
        return f"'''{value}'''"
    if not value:
        return "''''''"
    return value


def validate_key(key, lineno, path):
    key_part = key.split("#", 1)[0].rstrip(" ")

    extra_chars = set(key_part).difference(KEY_ALLOWED_SYMBOLS)
    if extra_chars:
        raise InvalidKey(
            'Invalid characters in the key %s: %s at file "%s:%s"'
            % (key_part, sorted(extra_chars), os.path.basename(path), lineno)
        )


def parse(path: str) -> Dict[str, Item]:
    """
    Parses file and do validation.
    """
    en_path = os.path.join(os.path.dirname(path), EN)

    translations = {}
    inner_used_tags = set()
    with open(path, encoding="utf8") as f:
        lines = (line.strip("\n") for line in f)
        next(lines)  # title

        is_key = False
        is_value = False
        key = None
        value = True
        pre_comment = []
        inline_comment = None
        for lineno, line in enumerate(lines, start=1):
            if not is_value:
                if not line.strip():
                    pre_comment.clear()
                    continue
            if line.startswith("#"):
                if not is_key:
                    pre_comment.append(line)
                continue
            elif not is_key:
                split = line.split("#", 1)
                key = split[0].rstrip(" ")
                inline_comment = split[1].strip("# ") if len(split) > 1 else None
                is_key = True
                validate_key(key, lineno, path)
            else:
                if not is_value:
                    value = line
                    if line.startswith("'''") and not (line.rstrip().endswith("'''") and len(line) > 3):
                        is_value = True
                        value += "\n"
                else:
                    if line.rstrip().endswith("'''"):
                        value += line
                        is_value = False
                    else:
                        value += line + "\n"
                if not is_value:
                    is_key = False
                    tags = tag.findall(value)
                    for prefix, tag_name in tags:
                        inner_used_tags.add(tag_name)
                    assert key not in translations, f'Duplicate key "{key}" in {path}'
                    if value.startswith("'''") and value.rstrip().endswith("'''"):
                        value = value[3:-3]
                    translations[key] = Item(key, value, tuple(pre_comment), inline_comment)
                    pre_comment.clear()
    inner_tags = inner_used_tags.difference(translations)
    # Inner keys may not present in translation, in that case they should be present in en file
    # Skip next check if we already found all tags
    if path != en_path and inner_tags:
        en = parse(en_path)
        inner_tags = inner_tags.difference(en)
        other_unique_keys = set(translations) - set(en) - inner_used_tags
        if other_unique_keys:
            keys = ", ".join(sorted(other_unique_keys))
            raise UnusedKey(f"Unused keys: {keys}")

    if inner_tags:
        raise UnknownReference(
            "[%s] Reference to unknown tag(s) present: %s" % (os.path.basename(path), sorted(inner_tags))
        )
    return translations


def compare(en_path, other):
    en_dict = parse(en_path)
    other_dict = parse(other)
    en_key_set = set(en_dict)
    other_key_set = set(other_dict)
    only_en = en_key_set.difference(other_key_set)
    only_other = other_key_set.difference(en_key_set)
    print(f"==== Present only in {en_path}")
    for key in only_en:
        print(key)
        print(en_dict[key])
        print()

    print(f"==== Present only in {other}")
    for key in only_other:
        print(key)

    for key in en_key_set.intersection(other_key_set):
        if en_dict[key] == other_dict[key]:
            print(f'values for "{key}" are equals: {en_dict[key]}')


def make_copy(source, dest=None, for_translation=True):
    """
    Traverse over en file and replace en translation with the translations from source file.

    :param source: source file path
    :param dest: dest path to save file, if None, replace source
    :param for_translation:
    :return:
    """

    if dest is None:
        dest = source
    result = []
    en_path = os.path.join(os.path.dirname(source), "en.txt")
    en = parse(en_path)

    # Read header
    with open(source, encoding="utf8") as f:
        lines = iter(f)
        result.append(next(f).strip())
        for line in lines:
            line = line.strip()
            if not line:
                result.append("")
            elif line.startswith("#"):
                if line[1:] in en:
                    break
                result.append(line)
            else:
                break

    other = parse(source)

    with open(en_path, encoding="utf8") as f:
        lines = (line.strip("\n") for line in f)
        next(lines)  # title
        is_key = False
        key_was_not_added = False
        is_value = False
        key = None
        value = True
        # Read header
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            else:
                key = line
                is_key = True
                break
        for lineno, line in enumerate(lines, start=1):
            if not is_value and not line.strip() or line.startswith("#"):
                # dont add line after skipped key
                if not is_key and not line.strip() and key_was_not_added:
                    key_was_not_added = False
                    continue
                result.append(line)
            elif not is_key:
                key = line
                is_key = True
                validate_key(key, lineno, en_path)
                assert KEY_ALLOWED_SYMBOLS.issuperset(key), key
            else:
                if not is_value:
                    value = line
                    if line.startswith("'''") and not (line.rstrip().endswith("'''") and len(line) > 3):
                        value += "\n"
                        is_value = True
                else:
                    if line.rstrip().endswith("'''"):
                        value += line
                        is_value = False
                    else:
                        value += line + "\n"

                if not is_value:
                    is_key = False
                    if key in other:
                        translated_item = other[key]
                        # Don't add value that same as in en
                        if (
                                not translated_item.is_translated()
                                and value_for_string_table(value) == value_for_string_table(translated_item.value)
                                and not for_translation
                        ):
                            continue
                        result.append(translated_item.get_key_display())
                        result.append(value_for_string_table(translated_item.value))
                    else:
                        if for_translation:
                            result.append("f#{key}")
                            result.append("#%s" % "\n#".join(value_for_string_table(value).split("\n")))
                        else:
                            key_was_not_added = True

    # add new line at end of file
    if result[-1]:
        result.append("")

    with open(dest, "w", encoding="utf8") as f:
        f.write("\n".join(result))

    # validate result
    parse(dest)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("command", help="full | small | check", choices=["full", "small", "check"])
    parser.add_argument("input")
    parser.add_argument("output", nargs="?")
    args = parser.parse_args()
    if not os.path.exists(args.input):
        print("Input {args.input} does not exists")
        exit(1)
    if args.command == "full":
        if os.path.exists(args.output):
            print("Output file mush not exists")
            exit(1)
        make_copy(args.input, args.output, for_translation=True)
        print("Full copy created", args.output)
        exit(0)
    elif args.command == "small":
        make_copy(args.input, args.output, for_translation=False)
        print("Small copy created", args.output)
        exit(0)
    elif args.command == "check":
        parse(args.input)
        print("Checked", args.input)
        exit(0)
    print("Unknown command")
    exit(1)
