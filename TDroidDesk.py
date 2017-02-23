# coding: utf-8

import os
import sys
import zipfile

from argparse import ArgumentParser


BACKGROUND_FILE = 'background.jpg'
COLORS_FILE = 'colors.tdesktop-theme'
THEME_MAP_FILE = 'theme-map.ini'
TEMP_DIR = 'tmp'

THEME = 'theme'
BACKGROUND = 'background'

DESCRIPTION = 'Convert Telegram Android theme to Telegram Desktop ones.'

SINGLE_COMMENT_CHARS = ['//', ';', '#']
THEME_MAP_SEPARATOR = '='
ATTHEME_SEPARATOR = '='

DESKTOP_KEYS_FILE = 'desktop.keys'
ANDROID_KEYS_FILE = 'android.keys'

STATE_READ_THEME = 0
STATE_READ_BACKGROUND = 1


def main():
    arg_parser = create_arg_parser()
    return parse_args(arg_parser)


def create_arg_parser():
    parser = ArgumentParser(prog='TDroidDesk', description=DESCRIPTION)
    parser.add_argument(dest='theme', help='theme to convert')
    return parser


def parse_args(arg_parser):
    args = arg_parser.parse_args()

    theme = args.theme
    if os.path.isfile(theme):
        attheme = open_attheme(theme)
        desktop_theme = convert_att_desktop(attheme)
        save_desktop_theme(desktop_theme, os.path.splitext(theme)[0])
    elif os.path.isdir(theme):
        arg_parser.error('{0} is a directory'.format(theme))
        return 1
    else:
        arg_parser.error('{0} does not exist'.format(theme))
        return 2
    return 0


def open_attheme(attheme_path):
    state = STATE_READ_THEME

    attheme = get_empty_theme()
    with open(attheme_path, 'rb') as fp:
        # TODO: read embed image
        while True:
            if state == STATE_READ_THEME:
                line = fp.readline().decode('ascii')

                # Reached EOL
                if not line:
                    break

                if 'WPS' in line:
                    state = STATE_READ_BACKGROUND
                    continue

                if is_key_val_pair(line, ATTHEME_SEPARATOR):
                    key, raw_color = line.strip().split(ATTHEME_SEPARATOR, 1)
                    color = convert_signed_int(int(raw_color))

                    attheme[THEME][key] = color
            elif state == STATE_READ_BACKGROUND:
                buf = fp.read(1024)
                if buf:
                    # FIXME: Ignore WPE tag
                    # if is_end_of_background(buf):
                    #    break

                    attheme[BACKGROUND].extend(buf)
                else:
                    # malformed theme, ignore background image
                    break

    return attheme


def save_desktop_theme(desktop_theme, filename):
    with open(COLORS_FILE, 'w') as fp:
        for key, color in desktop_theme[THEME].items():
            fp.write('{0}: #{1:x};\n'.format(key, color))

    with open(BACKGROUND_FILE, 'wb') as fp:
        fp.write(desktop_theme[BACKGROUND])

    desktop_theme_file = '{0}.tdesktop-theme'.format(filename)
    with zipfile.ZipFile(desktop_theme_file, mode='w') as zp:
        zp.write(COLORS_FILE)
        zp.write(BACKGROUND_FILE)

    os.remove(COLORS_FILE)
    os.remove(BACKGROUND_FILE)


def convert_att_desktop(attheme):
    theme_map = get_theme_map()
    desktop_theme = get_empty_theme()

    for desktop_key, att_key in theme_map.items():
        if att_key not in attheme[THEME]:
            # print('Missing {0} key in source theme'.format(att_key))
            continue

        color = attheme[THEME][att_key]
        desktop_theme[THEME][desktop_key] = color

    desktop_theme[BACKGROUND] = attheme[BACKGROUND]

    return desktop_theme


def get_theme_map():
    theme_map = {}
    desktop_keys = get_desktop_theme_keys()
    android_keys = get_android_theme_keys()

    with open(THEME_MAP_FILE, 'r') as fp:
        for line in fp.readlines():
            if is_comment(line):
                continue

            if is_key_val_pair(line, THEME_MAP_SEPARATOR):
                desktop_key, android_key = line.strip().split('=', 1)
                if desktop_key not in desktop_keys:
                    print('Warning: unknown key: {0}'.format(desktop_key))
                if android_key not in android_keys:
                    print('Warning: unknown key: {0}'.format(android_key))

                theme_map[desktop_key] = android_key

    return theme_map


def get_empty_theme():
    return {
        'theme': {},
        'background': bytearray()
    }


def get_android_theme_keys():
    return get_theme_keys(ANDROID_KEYS_FILE)


def get_desktop_theme_keys():
    return get_theme_keys(DESKTOP_KEYS_FILE)


def get_theme_keys(filename):
    theme_keys = []

    with open(filename, 'r') as fp:
        theme_keys = [line.strip() for line in fp if line]

    return theme_keys


def is_comment(line):
    for char in SINGLE_COMMENT_CHARS:
        if char in line:
            return True
    return False


def is_key_val_pair(line, sep):
    return sep in line


def is_end_of_background(buf):
    return buf.endswith(b'WPE\n') or buf.endswith(b'WPE')


def convert_signed_int(value):
    rgb = (value + 0x100000000)

    a = (rgb & 0xFF000000) >> 24
    r = (rgb & 0x00FF0000) >> 16
    g = (rgb & 0x0000FF00) >> 8
    b = (rgb & 0x000000FF)

    return (r << 24) | (g << 16) | (b << 8) | a


if __name__ == '__main__':
    sys.exit(main())
