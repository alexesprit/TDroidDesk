# coding: utf-8

"""Convert Telegram Android theme to Telegram Desktop ones."""

import glob
import os
import sys
import zipfile

from argparse import ArgumentParser
from PIL import Image


BACKGROUND_FILE = 'background.jpg'
TILED_FILE = 'tiled.png'
COLORS_FILE = 'colors.tdesktop-theme'
THEME_MAP_FILE = 'theme-map.ini'
TRANSPARENCE_MAP_FILE = 'transparency-map.ini'

ATTHEME_WILDCARD = '*.attheme'
DESKTOP_THEME_FILENAME = '{0}.tdesktop-theme'

TEMP_FILES = (BACKGROUND_FILE, TILED_FILE, COLORS_FILE)

THEME = 'theme'
BACKGROUND = 'background'

TILED_BACKGROUND_SIZE = (100, 100)

ATT_BACKGROUND_KEY = 'chat_wallpaper'

DESCRIPTION = 'Convert Telegram Android theme to Telegram Desktop ones.'

SINGLE_COMMENT_CHARS = ['//', ';', '#']
THEME_MAP_SEPARATOR = '='
ATTHEME_SEPARATOR = '='

DESKTOP_KEYS_FILE = 'desktop.keys'
ANDROID_KEYS_FILE = 'android.keys'

STATE_READ_THEME = 0
STATE_READ_BACKGROUND = 1


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
    if not theme_path:
        convert_themes_in_cwd()
    elif os.path.isfile(theme_path):
        try:
            convert_theme(theme_path)
        except ValueError as e:
            print(str(e))
    elif os.path.isdir(theme_path):
        arg_parser.error('{0} is a directory'.format(theme_path))
        return 1
    else:
        arg_parser.error('{0} does not exist'.format(theme_path))
        return 2
    return 0


def convert_themes_in_cwd():
    """Convert all Android themes in current working directory."""
    for theme_path in glob.iglob(ATTHEME_WILDCARD):
        try:
            convert_theme(theme_path)
        except ValueError as err:
            print(str(err))


def convert_theme(theme_path):
    """Convert Android theme.

    Arguments:
    theme_path - path to Android theme file
    """
    theme_name = os.path.splitext(theme_path)[0]
    print('Converting {0}...'.format(theme_name))

    try:
        attheme = open_attheme(theme_path)
    except UnicodeDecodeError:
        raise ValueError('Error: invalid theme file: {0}'.format(theme_path))

    desktop_theme = convert_att_desktop(attheme)
    save_desktop_theme(desktop_theme, theme_name)

    print('Done converting {0}'.format(theme_name))


def open_attheme(attheme_path):
    """Read Android theme and return object that describes the theme.

    Arguments:
    theme_path - path to Android theme file
    """
    state = STATE_READ_THEME

    attheme = get_empty_theme()
    with open(attheme_path, 'rb') as fp:
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
                    key, color = parse_theme_line(line)

                    attheme[THEME][key] = color
            elif state == STATE_READ_BACKGROUND:
                buf = fp.read(1024)
                if buf:
                    attheme[BACKGROUND].extend(buf)
                else:
                    # malformed theme or the end of stream
                    break

    if not attheme[BACKGROUND]:
        if ATT_BACKGROUND_KEY in attheme[THEME]:
            attheme[BACKGROUND] = attheme[THEME][ATT_BACKGROUND_KEY]
        else:
            print('Warning: missing background in source theme')

    return attheme


def parse_theme_line(line):
    """Parse single line of theme file.

    Arguments:
    line - line that contains key-val pair.
    """
    key, raw_color = line.strip().split(ATTHEME_SEPARATOR, 1)
    try:
        color = read_color(raw_color)
        return key, color
    except ValueError:
        raise ValueError(
            'Invalid color: {0}={1}'.format(key, raw_color))


def save_desktop_theme(desktop_theme, filename):
    """Save desktop theme object to desktop theme format.

    Arguments:
    desktop_theme - object that represents desktop theme
    filename - path to file to save
    """
    remove_temp_files()

    with open(COLORS_FILE, 'w') as fp:
        for key, color in desktop_theme[THEME].items():
            fp.write('{0}: #{1:08x};\n'.format(key, color))

    background = desktop_theme[BACKGROUND]
    if isinstance(background, bytearray):
        with open(BACKGROUND_FILE, 'wb') as fp:
            fp.write(background)
    elif (isinstance(background, int)):
        get_background_from_color(background).save(TILED_FILE, 'PNG')

    desktop_theme_file = DESKTOP_THEME_FILENAME.format(filename)
    with zipfile.ZipFile(desktop_theme_file, mode='w') as zp:
        write_file_to_zip(zp, TILED_FILE)
        write_file_to_zip(zp, COLORS_FILE)
        write_file_to_zip(zp, BACKGROUND_FILE)

    remove_temp_files()


def convert_att_desktop(attheme):
    """Create object that describes desktop theme.

    Arguments:
    attheme - object that represents Android theme
    """
    theme_map = get_theme_map()
    transparency_map = get_transparency_map()
    desktop_theme = get_empty_theme()

    for desktop_key, att_key in theme_map.items():
        if att_key not in attheme[THEME]:
            # print('Missing {0} key in source theme'.format(att_key))
            continue

        color = attheme[THEME][att_key]
        if desktop_key in transparency_map:
            alpha = transparency_map[desktop_key]
            color = apply_transparency(color, alpha)

        desktop_theme[THEME][desktop_key] = color

    desktop_theme[BACKGROUND] = attheme[BACKGROUND]

    return desktop_theme


def get_theme_map():
    """Return dict that maps dekstop theme keys to Android theme ones."""
    theme_map = get_map(THEME_MAP_FILE)
    desktop_keys = get_desktop_theme_keys()
    android_keys = get_android_theme_keys()

    for desktop_key, android_key in theme_map.items():
        if desktop_key not in desktop_keys:
            print('Warning: unknown key: {0}'.format(desktop_key))
        if android_key not in android_keys:
            print('Warning: unknown key: {0}'.format(android_key))

        theme_map[desktop_key] = android_key

    return theme_map


def get_transparency_map():
    """Return dict that contains transparency lever for colors."""
    def read_alpha(key, val):
        if (is_number(val)):
            return int(val, 16)

        raise ValueError(
            'Invalid transparency value: {0}={1}'.format(key, val))

    return get_map(TRANSPARENCE_MAP_FILE, read_alpha)


def get_map(filepath, func=None):
    """Return dict that maps keys to values.

    Arguments:
    filepath - path to file contains map
    func - function that is called for each map value
    """
    raw_map = {}
    with open(filepath, 'r') as fp:
        for line in fp.readlines():
            if is_comment(line):
                continue

            if is_key_val_pair(line, THEME_MAP_SEPARATOR):
                key, val = line.strip().split('=', 1)
                if func:
                    val = func(key, val)
                raw_map[key] = val

    return raw_map


def get_empty_theme():
    """Create object that contains empty theme."""
    return {
        'theme': {},
        'background': bytearray()
    }


def get_background_from_color(color):
    """Create image based on given color.

    Arguments:
    color - color in RGBA format
    """
    r, g, b, a = get_rgba_from_color(color)
    return Image.new('RGB', TILED_BACKGROUND_SIZE, (r, g, b))


def get_android_theme_keys():
    """Return list of Android theme keys."""
    return get_theme_keys(ANDROID_KEYS_FILE)


def get_desktop_theme_keys():
    """Return list of desktop theme keys."""
    return get_theme_keys(DESKTOP_KEYS_FILE)


def get_theme_keys(filename):
    """Return list of theme keys.

    Arguments:
    filename - path to file where keys are stored
    """
    theme_keys = []

    with open(filename, 'r') as fp:
        theme_keys = [line.strip() for line in fp if line]

    return theme_keys


def remove_temp_files():
    """Remove temporary files that are used during converting."""
    for filepath in TEMP_FILES:
        if os.path.exists(filepath):
            os.remove(filepath)


def write_file_to_zip(zp, filepath):
    """Add file to given zip object. Do nothing is file is not exist.

    Arguments:
    zp - zip object
    filepath - path to file to add
    """
    if os.path.exists(filepath):
        zp.write(filepath)


def is_comment(line):
    """Check if line contains comment.

    Arguments:
    line - single line of file
    """
    for char in SINGLE_COMMENT_CHARS:
        if char in line:
            return True
    return False


def is_key_val_pair(line, sep):
    """Check if line contains key=val pair.

    Arguments:
    line - single line of file
    sep - separator
    """
    return sep in line


def read_color(raw_color):
    """Read raw color and return integer representation of color.

    Arguments:
    raw_color - string that contains color
    """
    if (is_number(raw_color)):
        return argb2rgba(int(raw_color))
    elif raw_color.startswith('#'):
        return int(raw_color[1:], 16)
    else:
        raise ValueError('Invalid color: {0}'.format(raw_color))


def apply_transparency(color, alpha):
    """Apply transparency level to given color in RGB format."""
    return (color & 0xFFFFFF00) | (alpha)


def is_number(string):
    """Check if given string is a number.

    Arguments:
    string - string that supposed to have number
    """
    try:
        complex(string)
    except ValueError:
        return False

    return True


def argb2rgba(argb):
    """Convert color from ARGB to RGBA format.

    Arguments:
    argb - color in ARGB format
    """
    a, r, g, b = get_argb_from_color(argb)

    return (r << 24) | (g << 16) | (b << 8) | a


def get_argb_from_color(argb):
    """Return typle of A, R, G, B components from given color.

    Arguments:
    rgb - color
    """
    a = (argb & 0xFF000000) >> 24
    r = (argb & 0x00FF0000) >> 16
    g = (argb & 0x0000FF00) >> 8
    b = (argb & 0x000000FF)

    return a, r, g, b


def get_rgba_from_color(rgba):
    """Return typle of R, G, B, A components from given color.

    Arguments:
    rgba - color
    """
    r = (rgba & 0xFF000000) >> 24
    g = (rgba & 0x00FF0000) >> 16
    b = (rgba & 0x0000FF00) >> 8
    a = (rgba & 0x000000FF)

    return r, g, b, a


if __name__ == '__main__':
    sys.exit(main())
