# main/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def filename(value):
    """Returns just the filename from a full path."""
    import os
    return os.path.basename(value)