import sys
from StringIO import StringIO
import email
from email.utils import parseaddr

from django.test import TestCase
from django.http import QueryDict
from django.test.client import Client

from mail.models import CustomUser
from mail.forms import MessageForm
from mail.forms import Mail
import settings
from process_mail import make_response_from_file

class MailTestCase(TestCase):
    def setUp(self):
        pass
        
    def testCustomUserModelProxy(self):
        user = CustomUser.objects.create(email="bar@baz.com",
                                         username="bar@baz.com")
        proxy_email = user.proxy_email.proxy_email
        self.assertNotEqual(proxy_email, None)

    def testSimpleMessageForm(self):
        data = QueryDict("").copy()
        data.update({'mto':'1@baz.com',
                     'mfrom':'2@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MessageForm(None, data)
        self.assertTrue(form.is_valid())
        message = form.save()
        self.assertEquals(message.mto.email, data['mto'])
        self.assertEquals(message.mfrom.email, data['mfrom'])

        # sending the same message twice is OK
        data.update({'mto':'1@baz.com',
                     'mfrom':'2@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MessageForm(None, data)
        self.assertTrue(form.is_valid())
        message = form.save()
        self.assertFalse(message.approved)
        
        # now try with a userfo who's unmoderated
        user = CustomUser.objects.create(email="3@baz.com",
                                         username="3@baz.com",
                                         needs_moderation=False)
        data.update({'mto':'1@baz.com',
                     'mfrom':'3@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MessageForm(None, data)
        self.assertTrue(form.is_valid())
        message = form.save()
        self.assertTrue(message.approved)

    def testSignupWorkflow(self):
        data = {'mto':'4@baz.com',
                'mfrom':'5@baz.com',
                'subject':'Hello',
                'message':'Hi'}
        
        c = Client()
        response = c.post('/write', data, follow=True)
        self.assertContains(response, "Repeat password")

        data = {'email':response.context['message'].mfrom.email,
                'password':'asd',
                'repeat_password':'asd'}

        response = c.post(response.request['PATH_INFO'],
                          data,
                          follow=True)
        self.assertTemplateUsed(response, 'preview.html')
        
        
    def testEmailParsing(self):
        # create an initial "from" email
        message = email.message_from_file(
            open("./testdata/mail3.txt", "r"))
        name, mto = parseaddr(message['to'])
        name, mfrom = parseaddr(message['from'])
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue # it's just a container
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                break
        try:
            user = CustomUser.objects.get(
                email=mfrom)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create(email=mfrom,
                                             username=mfrom)
            user.set_unusable_password()
            user.save()
        recipient, _ = CustomUser.objects.get_or_create(
            email=mto,
            username=mto)
        message = Mail.objects.create(
            subject=message['subject'],
            mfrom=user,
            mto=recipient,
            message=body)

        # now we simulate a reply, and override a couple of relevant
        # headers 
        response = email.message_from_file(
            open("./testdata/mail4.txt", "r"))
        new_mto = "%s%s@foo.com" % (settings.MAIL_PREFIX,
                                    user.proxy_email.proxy_email)
        response.replace_header('in-reply-to', "<%s>" % message.message_id)
        response.replace_header('references', "<%s>" % message.message_id)
        response.replace_header('to', "%s <%s>" % (message.message_id,
                                      new_mto))
        fp = StringIO(response.as_string()) 
        response = make_response_from_file(fp)
        self.assertTrue(response)
        
        # now parse in an email that isn't a response to anything
        response = email.message_from_file(
            open("./testdata/mail2.txt", "r"))
        response = make_response_from_file(fp)
        self.assertFalse(response)
