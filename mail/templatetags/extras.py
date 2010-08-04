import re
from sets import Set
from datetime import datetime, timedelta

from django import template
from django.template import Node
from django.utils.html import escape

from shorten.models import Shortened

register = template.Library()
 
MOMENT = 120    # duration in seconds within which the time difference 
                # will be rendered as 'a moment ago'


def _quote_normalise(line):
    SKIP = " >|"
    cleaned = ""
    for letter in line:
        if letter in SKIP:
            continue
        cleaned += letter
    return cleaned

def _has_collapsable(line):
    """Return true if the line provided contains text that suggests it
    should be collapsed
    """
    line = line.strip()
    quote_prefix_1 = r"^On .+ (wrote|said):"
    quote_prefix_2 = r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}.+ (wrote|said):"
    quote_prefix_3 = r"^>"
    original_message = r"^----*\s"
    our_system_footer = "PLEASE NOTE"
    
    empty_quote = r"^>\s*$"
    sigs = [quote_prefix_1,
            quote_prefix_2,
            quote_prefix_3,
            original_message,
            empty_quote,
            our_system_footer]
    found = False
    for sig in sigs:
        found = re.search(sig, line, re.I)
        if found:
            break
    return bool(found)

@register.filter
def collapsequotes(message):
    """Usage: {{ message|collapsequotes }}

    Add a <span> around lines that should be collapsed; either lines
    we've seen before, or lines that include suggestive text.
    """
    parent = message.in_reply_to
    seen = Set()
    mylines = []
    while parent:
        for parentline in parent.message.splitlines():
            normalised = _quote_normalise(parentline)
            if normalised:                
                seen.add(normalised)
        parent = parent.in_reply_to
    collapsing = False
    for line in message.message.splitlines():
        norm_line = _quote_normalise(line)
        should_collapse = _has_collapsable(line) \
                          or norm_line in seen \
                          or (not line.strip() and collapsing)
        if not collapsing and should_collapse:
            collapsing = True
            line = '<div class="uncollapse">- show quoted text -</div> <span class="collapsed">%s' % escape(line)
        elif collapsing and not should_collapse:
            collapsing = False
            line = '</span>%s' % escape(line)
        else:
            line = escape(line)
        mylines.append(line)
    return "\n".join(mylines)            


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
@register.filter

def truncateletters(value, arg):
    """
    Truncates a string after a certain number of letters
    
    Argument: Number of letters to truncate after
    """

    try:
        length = int(arg)
    except ValueError: # invalid literal for int()
        return value # Fail silently
    if not isinstance(value, basestring):
        value = str(value)

    if len(value) > length:
        truncated = value[:length]
        if not truncated.endswith('...'):
            truncated += '...'
        return truncated

    return value

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
