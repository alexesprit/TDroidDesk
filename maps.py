# coding: utf-8

"""Theme maps."""

import util

THEME_MAP_FILE = 'theme-map.ini'
TRANSPARENCE_MAP_FILE = 'transparency-map.ini'

THEME_MAP_SEPARATOR = '='


def get_theme_map():
    """Return dict that maps dekstop theme keys to Android theme ones."""
    return get_map(THEME_MAP_FILE)


def get_transparency_map():
    """Return dict that contains transparency lever for colors."""
    def read_alpha(key, val):
        """Read alpha level from string."""
        try:
            return int(val, 16)
        except ValueError:
            print('Warning: invalid transparency value: {0}={1}'.format(
                key, val))
            return None

    return get_map(TRANSPARENCE_MAP_FILE, read_alpha)


def get_map(filepath, func=None):
    """Return dict that maps keys to values.

    If 'func' parameter is defined, a function value will be used as
    a key value. If function returns 'None', the key will be ignored.

    Arguments:
    filepath - path to file contains map
    func - function that is called for each map value
    """
    raw_map = {}
    with open(filepath, 'r') as fp:
        for line in fp.readlines():
            if util.is_comment(line):
                continue

            if util.is_key_val_pair(line, THEME_MAP_SEPARATOR):
                key, val = line.strip().split('=', 1)
                if func:
                    val = func(key, val)
                    if val is None:
                        continue
                raw_map[key] = val

    return raw_map


def check_maps(theme_map, trans_map):
    """Check given maps for possible errors."""
    desktop_keys = util.get_desktop_theme_keys()
    android_keys = util.get_android_theme_keys()

    for desktop_key, android_key in theme_map.items():
        if desktop_key not in desktop_keys:
            print('Warning: unknown key in theme map: {0}'.format(desktop_key))
        if android_key not in android_keys:
            print('Warning: unknown key in theme map: {0}'.format(android_key))

    for key in trans_map:
        if key not in desktop_keys:
            print('Warning: unknown key in tranparency map: {0}'.format(key))
        elif key not in theme_map:
            print('Warning: transparency for {0} key will be ignored'.format(
                key))
            print(
                'Add this key to theme map or remove it from transparency map')
