from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Preserve all current query parameters except the ones being overridden.
    
    Usage:
      <a href="?{% url_replace sort='device_serial' %}">Sort by Serial</a>
    
    Keeps every other ?param intact, only replaces 'sort'. Pass a value of
    None or '' to remove a param entirely.
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ''):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()