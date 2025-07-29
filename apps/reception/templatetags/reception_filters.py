# apps/reception/templatetags/reception_filters.py

from django import template

register = template.Library()


@register.filter
def as_int(value):
    """Converts a string value to an integer, returning None if conversion fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None  # یا 0، بسته به اینکه می‌خواهید در صورت شکست چه برگردانده شود
