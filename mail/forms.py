from django.contrib.auth import authenticate
from django import forms

from akismet import Akismet

from models import CustomUser
from models import Mail
from utils import TemplatedForm
import settings

class MessageForm(TemplatedForm):
    mto = forms.EmailField(
        required=True,
        max_length=75)
    mfrom = forms.EmailField(
        required=True,
        max_length=75)
    subject = forms.CharField(
        required=True)
    message = forms.CharField(
        required=True,
        widget=forms.Textarea)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        return super(MessageForm, self).__init__(*args, **kwargs)

    def clean(self):
        if settings.AKISMET_KEY and not settings.OFFLINE:
            api = Akismet(settings.AKISMET_KEY,
                          agent="mailtrail")
            req = self.request.META
            data = {'user_ip':req['REMOTE_ADDR'],
                    'user_agent':req['HTTP_USER_AGENT'],
                    'referrer':req.get('HTTP_REFERER',''),
                    'comment_type':'email',
                    'comment_author_email':self.cleaned_data['mfrom'],
                    'server_name':req['SERVER_NAME'],
                    'http_accept':req['HTTP_ACCEPT']}
            spam = api.comment_check(self.cleaned_data['message'],
                                     data=data)
            if spam:
                raise forms.ValidationError('That looks too much like spam')
                
        return self.cleaned_data

    def save(self):
        # first get or create a user
        email=self.cleaned_data['mfrom']
        try:
            user = CustomUser.objects.get(
                email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create(email=email,
                                             username=email)
            user.set_unusable_password()
            user.save()
        # now create an email, and decide if it needs moderation
        recipient, created = CustomUser.objects.get_or_create(
            username=self.cleaned_data['mto'],
            email=self.cleaned_data['mto'])
        if created:
            recipient.set_unusable_password()
            recipient.save()
        message = Mail.objects.create(
            subject=self.cleaned_data['subject'],
            mfrom=user,
            mto=recipient,
            message=self.cleaned_data['message'],
            approved=not user.needs_moderation)
        message.save() # for some reason, needed to set id
        return message

    
class LoginForm(TemplatedForm):
    email = forms.EmailField(
        required=True,
        max_length=75)
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=True,
        label="Password")

    def clean(self):
        if 'email' in self.cleaned_data \
               and 'password' in self.cleaned_data:
            user = authenticate(username=self.cleaned_data['email'],
                                password=self.cleaned_data['password']) 
            if not user or not user.is_authenticated():
                raise forms.ValidationError('Your login details '
                                        'are incorrect')
        return self.cleaned_data
    
    def save(self):
        user = authenticate(username=self.cleaned_data['email'],
                            password=self.cleaned_data['password']) 
        return user
    

class RegisterForm(TemplatedForm):
    email = forms.EmailField(
        required=True,
        max_length=75)
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=True,
        label="Password")
    repeat_password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=True,
        label="Repeat password")

    def clean(self):
        if self.cleaned_data['password'] != \
           self.cleaned_data['repeat_password']:
            raise forms.ValidationError("The passwords don't match")
        return self.cleaned_data
    
    def save(self):
        user = CustomUser.objects.get(email=self.cleaned_data['email'])
        user.set_password(self.cleaned_data['password'])
        user.save()
        user = authenticate(username=self.cleaned_data['email'],
                            password=self.cleaned_data['password']) 
        return user
    
