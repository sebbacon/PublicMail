from datetime import datetime, timedelta

from django import template
from django.template import Node

from shorten.models import Shortened

register = template.Library()
 
MOMENT = 120    # duration in seconds within which the time difference 
                # will be rendered as 'a moment ago'

@register.filter
def percentage(fraction, population):
    """Usage: {{ fraction|percentage:'population' }}
    """
    try:  
        return "%.0f%%" % ((float(fraction) / float(population)) * 100)  
    except (ValueError, ZeroDivisionError):  
        return ""

@register.filter
def naturalTimeDifference(value):
    """Finds the difference between the datetime value given and now()
    and returns appropriate humanize form
    """

    if isinstance(value, timedelta):
        delta = value
    elif isinstance(value, datetime):
        delta = datetime.now() - value        
    else:
        delta = None

    if delta:
        if delta.days > 6:
            return value.strftime("%b %d") # May 15
        if delta.days > 1:
            return value.strftime("%A") # Wednesday
        elif delta.days == 1:
            return 'yesterday'
        elif delta.seconds >= 7200:
            return str(delta.seconds / 3600 ) + ' hours ago'
        elif delta.seconds >= 3600:
            return '1 hour ago' 
        elif delta.seconds > MOMENT:
            return str(delta.seconds/60) + ' minutes ago' 
        else:
            return 'a moment ago' 
    else:
        return str(value)

@register.tag(name="short_url")       
def short_url(parser, token):
    url = template.defaulttags.url(parser, token)
    return ShortenedUrlNode(url)

class ShortenedUrlNode(Node):
    def __init__(self, urlnode):
        self.urlnode = urlnode

    def render(self, context):
        url = self.urlnode.render(context)
        return Shortened.objects.make(url, "")
