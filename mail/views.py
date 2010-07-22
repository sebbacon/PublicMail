from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect as redirect
from django.core.urlresolvers import reverse

from utils import render
from utils import send_mail
from forms import LoginForm
from forms import RegisterForm
from forms import MailForm
from models import Mail


@render('home.html')
def home(request):
    return redirect(reverse('write'))


def _get_mail_list(request):
    if request.user.is_anonymous():
        mails = Mail.objects.filter(in_reply_to=None,
                                    approved=True)\
                                    .order_by('-last_modified')
    else:
        mails = request.user.mfrom.filter(in_reply_to=None)
    return mails

@render('write.html')
def write(request):
    mails = _get_mail_list(request)
    if request.method == "POST":
        form = MailForm(request, request.POST, request.FILES)
        if form.is_valid():
            mail = form.save()
            if request.user.is_anonymous() \
                   or request.user.email != mail.mfrom.email:
                return redirect(reverse('login_or_register_form',
                                        kwargs={'mail': mail.pk}))
            else:
                return redirect(reverse('posted',
                                        kwargs={'mail': mail.pk}))
    else:
        if request.user.is_anonymous():
            form = MailForm(request)
        else:
            form = MailForm(request,
                               initial={'mfrom':request.user.email})
    return locals()

@render('process_queue.txt')
def process_queue(request):
    mails = Mail.objects.filter(approved=True,
                                sent=None)\
               .order_by('created')[:10]
    done = []
    for mail in mails:
        output = send_mail(
            mail=mail,
            message=mail.message,
            subject=mail.subject,
            mfrom=mail.mfrom.proxy_email,
            mto=mail.mto.email,
            message_id=mail.message_id)
        mail.sent = datetime.now()
        mail.save()
        done.append((mail.subject, output))
    return locals()


        
@render('view_mail_thread.html')
def view_mail_thread(request, mail):
    mail = Mail.objects.get(pk=mail)
    mails = _get_mail_list(request)
    start = mail.start_of_thread()
    if request.method == "POST":
        form = MailForm(request, request.POST, request.FILES)
        if form.is_valid():
            mail = form.save()
            mail.in_reply_to = start.end_of_thread()
            mail.save()
            if request.user.is_anonymous():
                return redirect(reverse('login_or_register_form',
                                        kwargs={'mail': mail.pk}))
            else:
                return redirect(reverse('preview',
                                        kwargs={'mail': mail.pk}))
    else:
        if request.user.is_anonymous():
            form = MailForm(request)
        else:
            form = MailForm(request,
                               initial={'mfrom':request.user.email,
                                        'mto':start.mto.email,
                                        'subject':'Re: %s' % start.subject})
    if start == mail:
        return locals()
    else:
        return redirect(reverse('mail',
                                kwargs={'mail':start.id})\
                        + "#mail-%d" % mail.id)



@render('posted.html')
def posted(request, mail):
    mails = _get_mail_list(request)
    mail = Mail.objects.get(pk=mail)
    messages.info(request, ("Your email has been saved.  Please"
                            " check your inbox to confirm.\n\n\n"
                            " Meanwhile, why not write another one?"))
    return redirect(reverse('write'))

@render('preview.html')
def preview(request, mail):
    mails = _get_mail_list(request)
    mail = Mail.objects.get(pk=mail)
    if request.method == "POST":
        if request.POST.has_key('post'):
            mail.previewed = True
            mail.save()
            messages.info(request, ("Your email has been posted!"))
            return redirect(reverse('mail',
                                    kwargs={'mail':mail.id}))
        elif request.POST.has_key('delete'):
            messages.info(request, '"%s" deleted' \
                          % mail.subject)
            mail.delete()
            return redirect(reverse('write'))            
    return locals()

@render('approve.html')
def approve(request, mail, key):
    mails = _get_mail_list(request)
    mail = Mail.objects.get(pk=mail)
    if request.user.is_anonymous() or \
       request.user != mail.mfrom:
        url = reverse('approve',
                      kwargs={'mail':mail.id})
        messages.warning(request, ("You have to be logged in to "
                                   "approve this email"))
        return redirect('/login_form/?next=%s' % url)
    else:
        if key != mail.get_secret_key():
            messages.error(request,
                           "That was an invalid key")
        elif mail.approved:
            messages.error(request,
                           "You've already approved this message")
        else:
            mail.approved = True
            mail.save()
            messages.success(request, ("Thanks! Now do you definitely"
                                       " want to send it?"))
            return redirect(reverse('preview',
                                    kwargs={'mail':mail.id}))
        return redirect(reverse('write'))

@render('login_or_register_form.html')
def login_or_register_form(request, mail):
    logout(request)
    mail = Mail.objects.get(pk=mail)
    if mail.mfrom.has_usable_password():
        whichform = LoginForm
        action = "login"
    else:
        whichform = RegisterForm
        action = "register"
    if request.method == "POST":
        form = whichform(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse('posted',
                                    kwargs={'mail': mail.pk}))
    else:
        form = whichform(initial={'email':mail.mfrom.email})
    return locals()

@render('login_form.html')
def login_form(request):
    if request.method == "POST":
        form = LoginForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            url = request.GET.get('next', reverse('write'))
            return redirect(url)
    else:
        form = LoginForm()
    return locals()

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out")
    return redirect(reverse('write'))
