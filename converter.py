# coding: utf-8

"""Converter module."""

import util

THEME = 'theme'
BACKGROUND = 'background'


class ThemeConverter(object):
    """Object that converts themes using given map file."""

    def __init__(self, theme_map, transp_map):
        """Constructor."""
        self.theme_map = theme_map
        self.transp_map = transp_map

    def convert(self, source_theme):
        """Create object that describes desktop theme.

        Arguments:
        source_theme - theme object
        """
        target_theme = util.get_empty_theme()

        for desktop_key, att_key in self.theme_map.items():
            if att_key not in source_theme[THEME]:
                # print('Missing {0} key in source theme'.format(att_key))
                continue

            color = source_theme[THEME][att_key]
            if desktop_key in self.transp_map:
                alpha = self.transp_map[desktop_key]
                color = util.apply_transparency(color, alpha)

            target_theme[THEME][desktop_key] = color

        target_theme[BACKGROUND] = source_theme[BACKGROUND]

        return target_theme
