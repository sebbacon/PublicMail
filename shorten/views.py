from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from models import Shortened

def index(request, key):
    shortened = get_object_or_404(Shortened, key=key)
    
    shortened.count += 1
    shortened.save()

    url = shortened.url
    return HttpResponseRedirect(url)

