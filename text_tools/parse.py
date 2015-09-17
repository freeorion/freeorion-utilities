import os
from argparse import ArgumentParser

import re

KEY_ALLOWED_SYMBOLS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789')

tag = re.compile('\[\[([a-z]+ )?(.+?)\]\]')
EN = 'en.txt'


def _check_key(key, lineno, path):
    reg = re.compile('([A-Z0-9_]+)( *# *translated)?$')
    match = reg.match(key)
    if not match:
        raise Exception('Key signature does not match %s[%s] for "%s"' % (os.path.basename(path), lineno, key))
    key = match.group(1)
    is_translated = bool(match.group(2))
    return key, is_translated


def parse(path):
    en_path = os.path.join(os.path.dirname(path), EN)

    translations = {}
    marked_as_translated = set()
    inner_used_tags = set()
    with open(path) as f:
        lines = (line.strip('\n') for line in f)
        next(lines)  # title

        is_key = False
        is_value = False
        key = None
        value = True
        for lineno, line in enumerate(lines, start=1):
            if not is_value and not line.strip() or line.startswith('#'):
                continue
            elif not is_key:
                key = line
                is_key = True
                key, is_translated = _check_key(key, lineno, path)
                if is_translated:
                    marked_as_translated.add(key)

                assert KEY_ALLOWED_SYMBOLS.issuperset(key), key
            else:
                if not is_value:
                    value = line
                    if line.startswith("'''") and not (line.rstrip().endswith("'''") and len(line) > 3):
                        is_value = True
                        value += '\n'
                else:
                    if line.rstrip().endswith("'''"):
                        value += line
                        is_value = False
                    else:
                        value += line + '\n'

                if not is_value:
                    is_key = False
                    tags = tag.findall(value)
                    for prefix, tag_name in tags:
                        inner_used_tags.add(tag_name)
                        # print value
                    assert key not in translations, 'Duplicate key "%s" in %s' % (key, path)
                    translations[key] = value
    inner_tags = inner_used_tags.difference(translations)
    if path != en_path:
        en, _ = parse(en_path)
        inner_tags = inner_tags.difference(en)

    assert not inner_tags, '[%s] Reference to unknown tag(s) present: %s' % (os.path.basename(path),
                                                                            sorted(inner_tags))
    for k, v in translations.items():
        if v.startswith("'''") and v.rstrip().endswith("'''"):
            translations[k] = v[3:-3]
    return translations, marked_as_translated


def compare(en_path, other):
    en_dict, _ = parse(en_path)
    other_dict, _ = parse(other)
    en_key_set = set(en_dict)
    other_key_set = set(other_dict)
    only_en = en_key_set.difference(other_key_set)
    only_other = other_key_set.difference(en_key_set)
    print '==== Present only in %s' % en_path
    for key in only_en:
        print key
        print en_dict[key]
        print

    print '==== Present only in %s' % other
    for key in only_other:
        print key

    for key in en_key_set.intersection(other_key_set):
        if en_dict[key] == other_dict[key]:
            print 'values for "%s" are equals: %s' % (key, en_dict[key])


def make_copy(other_path, result_path, other=None, add_comented=True):
    result = []
    en_path = os.path.join(os.path.dirname(other_path), 'en.txt')
    en, _ = parse(en_path)
    with open(other_path) as f:
        lines = iter(f)
        result.append(next(f).strip())
        for line in lines:
            line = line.strip()
            if not line:
                result.append('')
            elif line.startswith('#'):
                if line[1:] in en:
                    break
                result.append(line)
            else:
                break
    if not other:
        other, other_translated = parse(other_path)

    with open(en_path) as f:
        lines = (line.strip('\n') for line in f)
        next(lines)  # title
        is_key = False
        is_value = False
        key = None
        value = True
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            else:
                key = line
                is_key = True
                break

        for lineno, line in enumerate(lines, start=1):
            if not is_value and not line.strip() or line.startswith('#'):
                if line != result[-1]:
                    result.append(line)
            elif not is_key:
                key = line
                is_key = True
                key, _ = _check_key(key, lineno, en_path)
                assert KEY_ALLOWED_SYMBOLS.issuperset(key), key
            else:
                if not is_value:
                    value = line
                    if line.startswith("'''") and not (line.rstrip().endswith("'''") and len(line) > 3):
                        value += '\n'
                        is_value = True
                else:
                    if line.rstrip().endswith("'''"):
                        value += line
                        is_value = False
                    else:
                        value += line + '\n'

                if not is_value:
                    is_key = False
                    value = normalize_value(value)
                    if key in other:
                        if value == normalize_value(other[key]) and key not in other_translated:
                            continue
                        if key in other_translated:
                            result.append('%s  # translated' % key)
                        else:
                            result.append(key)
                        result.append(normalize_value(other[key]))
                    else:
                        if add_comented:
                            result.append('#%s' % key)
                            result.append('#%s' % '\n#'.join(value.split('\n')))

    # add new line at end of file
    if result[-1]:
        result.append('')

    with open(result_path, 'w') as f:
        f.write('\n'.join(result))
    parse(result_path)


def normalize_value(val):
    if val.startswith("'''") and val.endswith("'''"):
        val = val[3:-3]

    if '\n' in val or val.startswith((' ', '\t')) or val.endswith((' ', '\t')):
        return "'''%s'''" % val
    if not val:
        return "''''''"
    return val


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("command", help='full | small | check')
    parser.add_argument("input")
    parser.add_argument("output", nargs='?')
    args = parser.parse_args()
    if not os.path.exists(args.input):
        print 'Input %s does not exists' % args.input
        exit(1)
    if args.command == 'full':
        if os.path.exists(args.output):
            print "Output file mush not exists"
            exit(1)
        make_copy(args.input, args.output, add_english=True, remove_same=False)
        print "Full copy created", args.output
        exit(0)
    elif args.command == 'small':
        make_copy(args.input, args.output, add_english=False, remove_same=True)
        print "Small copy created", args.output
        exit(0)
    elif args.command == 'check':
        parse(args.input)
        print "Checked", args.input
        exit(0)
    print 'Unknown command'
    exit(1)


# def not_for_translate():
#     en = parse('en.txt')
#     # Base keys
#     keys = ['SITREP_PRIORITY_ORDER']
#
#     # Special keys
#     for k, v in en.items():
#         if re.search('''^[ 0-9%\(\)\[\]\{\}\-\+\*\=<>_'"]+$''', v):
#             print k
#             print v
#             print
#             keys.append(k)
#     print keys


