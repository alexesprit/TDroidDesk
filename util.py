# coding: utf-8

"""Helper functions."""

DESKTOP_KEYS_FILE = 'desktop.keys'
ANDROID_KEYS_FILE = 'android.keys'

SINGLE_COMMENT_CHARS = ['//', ';', '#']


def apply_transparency(color, alpha):
    """Apply transparency level to given color in RGB format."""
    return (color & 0xFFFFFF00) | (alpha)


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


def get_empty_theme():
    """Create object that contains empty theme."""
    return {
        'theme': {},
        'background': bytearray()
    }


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
