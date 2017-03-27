# coding: utf-8

"""Convert Telegram Android theme to Telegram Desktop ones."""

import glob
import os
import sys

from argparse import ArgumentParser

import maps
import theme
import util

from converter import ThemeConverter

ATTHEME_WILDCARD = '*.attheme'

DESCRIPTION = 'Convert Telegram Android theme to Telegram Desktop ones.'


def main():
    """Entry point."""
    arg_parser = create_arg_parser()
    return parse_args(arg_parser)


def create_arg_parser():
    """Create ArgumentParser object."""
    parser = ArgumentParser(prog='TDroidDesk', description=DESCRIPTION)
    parser.add_argument(dest='theme', nargs='?', help='theme to convert')
    return parser


def parse_args(arg_parser):
    """Parse arguments."""
    args = arg_parser.parse_args()

    theme_path = args.theme
    if theme_path:
        if os.path.isdir(theme_path):
            arg_parser.error('{0} is a directory'.format(theme_path))
            return 1
        elif not os.path.exists(theme_path):
            arg_parser.error('{0} does not exist'.format(theme_path))
            return 2

    theme_map = maps.get_theme_map()
    trans_map = maps.get_transparency_map()
    converter = ThemeConverter(theme_map, trans_map)

    maps.check_maps(theme_map, trans_map)
    convert_themes(theme_path, converter)
    return 0


def convert_themes(theme_path, converter):
    """Convert theme using given converter object."""
    if not theme_path:
        theme_paths = glob.iglob(ATTHEME_WILDCARD)
    else:
        theme_paths = (theme_path, )

    for theme_path in theme_paths:
        theme_name = os.path.splitext(theme_path)[0]
        print('Converting {0}...'.format(theme_name))

        try:
            attheme = theme.open_attheme(theme_path)
            desktop_theme = converter.convert(attheme)
            theme.save_desktop_theme(desktop_theme, theme_name)

            print('Done converting {0}'.format(theme_name))
        except ValueError as err:
            print('Error: {0}'.format(err))
        except UnicodeDecodeError:
            print('Invalid theme file: {0}'.format(theme_path))


if __name__ == '__main__':
    sys.exit(main())
