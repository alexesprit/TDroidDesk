# coding: utf-8

import codecs
import os
import sys
import zipfile

from argparse import ArgumentParser


COLORS_FILE = 'colors.tdesktop-theme'
THEME_MAP_FILE = 'theme.map'
TEMP_DIR = 'tmp'

DESCRIPTION = 'Convert Telegram Android theme to Telegram Desktop ones.'


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
    attheme = {}
    with codecs.open(attheme_path, 'r', 'cp1251') as fp:
        # TODO: read embed image
        while True:
            line = fp.readline()

            # Reached EOL
            if not line:
                break

            if 'WPS' in line:
                break

            if '=' not in line:
                continue

            key, raw_color = line.strip().split('=', 1)
            color = convert_signed_int(int(raw_color))

            attheme[key] = color

    return attheme


def save_desktop_theme(desktop_theme, filename):
    with open(COLORS_FILE, 'w') as fp:
        for key, color in desktop_theme.items():
            fp.write('{0}: #{1:x};\n'.format(key, color))

    desktop_theme_file = '{0}.tdesktop-theme'.format(filename)
    with zipfile.ZipFile(desktop_theme_file, mode='w') as zp:
        zp.write(COLORS_FILE)

    os.remove(COLORS_FILE)


def convert_att_desktop(attheme):
    theme_map = get_theme_map()
    desktop_theme = {}

    for desktop_key, att_key in theme_map.items():
        if att_key not in attheme:
            print('Missing {0} key in source theme'.format(att_key))
            continue

        color = attheme[att_key]
        desktop_theme[desktop_key] = color

    return desktop_theme


def get_theme_map():
    theme_map = {}

    with open(THEME_MAP_FILE, 'r') as fp:
        for line in fp.readlines():
            if '=' not in line:
                continue

            key, val = line.strip().split('=', 1)
            theme_map[key] = val

    return theme_map


def convert_signed_int(value):
    rgb = (value + 0x100000000)

    a = (rgb & 0xFF000000) >> 24
    r = (rgb & 0x00FF0000) >> 16
    g = (rgb & 0x0000FF00) >> 8
    b = (rgb & 0x000000FF)

    return (r << 24) | (g << 16) | (b << 8) | a


if __name__ == '__main__':
    sys.exit(main())
