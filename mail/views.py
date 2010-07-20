from datetime import datetime

from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect as redirect
from django.core.urlresolvers import reverse

from utils import render
from utils import send_mail
from forms import LoginForm
from forms import RegisterForm
from forms import MessageForm
from models import Mail
import settings

@render('home.html')
def home(request):
    return redirect(reverse('write'))

@render('write.html')
def write(request):
    if request.user.is_anonymous():
        messages = []
    else:
        messages = request.user.mfrom_set.filter(in_reply_to=None)
    if request.method == "POST":
        form = MessageForm(request, request.POST, request.FILES)
        if form.is_valid():
            message = form.save()
            if request.user.is_anonymous():
                return redirect(reverse('login_or_register_form',
                                        kwargs={'message': message.pk}))
            else:
                return redirect(reverse('preview',
                                        kwargs={'message': message.pk}))
    else:
        if request.user.is_anonymous():
            form = MessageForm(request)
        else:
            form = MessageForm(request,
                               initial={'mfrom':request.user.email})
    return locals()

@render('process_queue.txt')
def process_queue(request):
    messages = Mail.objects.filter(approved=True,
                                   sent=None)\
               .order_by('created')[:10]
    done = []
    for message in messages:
        output = send_mail(
            message=message.message,
            subject=message.subject,
            mfrom="%s%s" % (settings.MAIL_PREFIX,
                            message.mfrom.proxy_email.proxy_email),
            mto=message.mto.email,
            message_id=message.message_id)
        message.sent = datetime.now()
        message.save()
        done.append((message.subject, output))
    return locals()

        
@render('view_mail_thread.html')
def view_mail_thread(request, message):
    message = Mail.objects.get(pk=message)
    return locals()


@render('preview.html')
def preview(request, message):
    message = Mail.objects.get(pk=message)
    if request.method == "POST":
        message.previewed = True
        message.save()
    return locals()

@render('login_or_register_form.html')
def login_or_register_form(request, message):
    message = Mail.objects.get(pk=message)
    if message.mfrom.has_usable_password():
        whichform = LoginForm
    else:
        whichform = RegisterForm
    if request.method == "POST":
        form = whichform(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse('preview',
                                    kwargs={'message': message.pk}))
    else:
        form = whichform(initial={'email':message.mfrom.email})
    return locals()

@render('login_form.html')
def login_form(request):
    if request.method == "POST":
        form = LoginForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = LoginForm()
    return locals()

def logout_view(request):
    logout(request)
    return redirect("/")
