import settings

def global_vars(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    context['OFFLINE'] = settings.OFFLINE
    context['app_name'] = settings.APP_NAME
    return context
