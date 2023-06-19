# Copyright: (c) 2023, Fabio Bertagna <bertagna@puzzle.ch>, Puzzle ITC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Utilities for XML operations."""
from __future__ import (absolute_import, division, print_function)

from xml.etree.ElementTree import Element

__metaclass__ = type


def dict_to_etree(input_dict: dict) -> Element:
    """
    Generates a python dictionary to an ElementTree.Element.
    :param input_dict: dictionary with input data
    :return: generated ElementTree.Element
    """
    tag_name = list(input_dict.keys())[0]
    value = input_dict[tag_name]
    new_element = Element(tag_name)
    new_element.text = value
    return new_element
