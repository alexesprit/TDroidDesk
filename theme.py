# coding: utf-8

"""Theme-related code."""

import os
import zipfile

from PIL import Image

import util

STATE_READ_THEME = 0
STATE_READ_BACKGROUND = 1

ATTHEME_SEPARATOR = '='

THEME = 'theme'
BACKGROUND = 'background'

DESKTOP_THEME_FILENAME = '{0}.tdesktop-theme'

ATT_BACKGROUND_KEY = 'chat_wallpaper'
TILED_BACKGROUND_SIZE = (100, 100)

BACKGROUND_FILE = 'background.jpg'
TILED_FILE = 'tiled.png'
COLORS_FILE = 'colors.tdesktop-theme'
TEMP_FILES = (BACKGROUND_FILE, TILED_FILE, COLORS_FILE)


# Android theme

def open_attheme(attheme_path):
    """Read Android theme and return object that describes the theme.

    Arguments:
    theme_path - path to Android theme file
    """
    state = STATE_READ_THEME

    attheme = util.get_empty_theme()
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

                if util.is_key_val_pair(line, ATTHEME_SEPARATOR):
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


def read_color(raw_color):
    """Read raw color and return integer representation of color.

    Arguments:
    raw_color - string that contains color
    """
    if (util.is_number(raw_color)):
        return util.argb2rgba(int(raw_color))
    elif raw_color.startswith('#'):
        return util.argb2rgba(int(raw_color[1:], 16))
    else:
        raise ValueError('Invalid color: {0}'.format(raw_color))


# Desktop theme

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


def get_background_from_color(color):
    """Create image based on given color.

    Arguments:
    color - color in RGBA format
    """
    r, g, b, a = util.get_rgba_from_color(color)
    return Image.new('RGB', TILED_BACKGROUND_SIZE, (r, g, b))


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
