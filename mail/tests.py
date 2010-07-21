from StringIO import StringIO
import email
from email.utils import parseaddr

from django.test import TestCase
from django.http import QueryDict
from django.test.client import Client
from django.core import mail
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse

from mail.models import CustomUser
from mail.forms import MessageForm
from mail.forms import Mail
from process_mail import make_response_from_file
from process_mail import EX_NOUSER, EX_SOFTWARE, EX_NOINPUT

class MailTestCase(TestCase):
    def setUp(self):
        pass

    def testThreading(self):
        user = CustomUser.objects.create(email="admin@baz.com",
                                         username="admin@baz.com",
                                         needs_moderation=False)
        message1 = Mail.objects.create(
            subject="ho",
            mfrom=user,
            mto=user,
            message="for the life of a bear")
        
        message2 = Mail.objects.create(
            subject="tiddly pom",
            mfrom=user,
            mto=user,
            message="it goes on snowing",
            in_reply_to=message1)
        message1.save()
        message2.save()
        c = Client()
        response = c.get(reverse('mail',
                                 kwargs={'message':message1.pk}))
        self.assertContains(response, "tiddly pom")
        response = c.get(reverse('mail',
                                 kwargs={'message':message2.pk}))
        self.assertContains(response, "life of a bear")

        

    def testSendAndReply(self):
        user = CustomUser.objects.create(email="admin@baz.com",
                                         username="admin@baz.com",
                                         needs_moderation=False)
        data = QueryDict("").copy()
        SUBJECT = "Test Send And Reply"
        data.update({'mto':'1@baz.com',
                     'mfrom':user.email,
                     'subject':SUBJECT,
                     'message':'Hi'})
        form = MessageForm(None, data)
        self.assertTrue(form.is_valid())
        message = form.save()
        c = Client()
        response = c.get('/process', follow=True)
        self.assertContains(response, SUBJECT)
        self.assertEquals(mail.outbox[0].subject, SUBJECT)
        message_id = mail.outbox[0].extra_headers['Message-ID']
        REPLY_SUBJECT = "Re: %s" % SUBJECT
        response = EmailMessage(REPLY_SUBJECT,
                                "Hello back",
                                "11@baz.com",
                                [user.proxy_email],
                                headers={'In-Reply-To':'<%s>' % message_id})
        response.send()
        self.assertEquals(mail.outbox[-1].subject, REPLY_SUBJECT)
        reply_fp = StringIO(mail.outbox[-1].message().as_string())
        response = make_response_from_file(reply_fp)
        self.assertTrue(response)

        mails = Mail.objects.order_by('created')
        self.assertEqual(mails[0].reply, mails[1])

    def testCustomUserModelProxy(self):
        user = CustomUser.objects.create(email="bar@baz.com",
                                         username="bar@baz.com")
        self.assertNotEqual(user.proxy_email, None)

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
        write_data = {'mto':'4@baz.com',
                'mfrom':'5@baz.com',
                'subject':'Hello',
                'message':'Hi'}
        
        c = Client()
        # first time they visit, they should get to the register form
        response = c.post(reverse('write'), write_data, follow=True)
        self.assertContains(response, "Repeat password")

        reg_data = {'email':response.context['message'].mfrom.email,
                'password':'asd',
                'repeat_password':'asd'}
        response = c.post(response.request['PATH_INFO'],
                          reg_data,
                          follow=True)
        # now check previewing
        self.assertTemplateUsed(response, 'preview.html')
        message = Mail.objects.get()
        self.assertFalse(message.previewed)
        c.post(reverse('preview', kwargs={'message':message.pk}))
        message = Mail.objects.get()
        self.assertTrue(message.previewed)

        # and when you're logged in and you write an email, you should
        # go straight to the preview page
        response = c.post(reverse('write'), write_data, follow=True)
        self.assertTemplateUsed(response, 'preview.html')

        # test logging out
        response = c.get('/logout', follow=True)
        self.assertNotContains(response, 'started the following')
        
        # they should see the login rather than register form this
        # time
        response = c.post(reverse('write'), write_data, follow=True)
        self.assertNotContains(response, "Repeat password")
        response = c.get('/logout', follow=True)
        
        # now test going direct to login form
        data = {'email': '5@baz.com',
                'password': 'asd'}
        response = c.get(reverse('login_form'))
        response = c.post(reverse('login_form'), data, follow=True)
        self.assertContains(response, 'started the following')
        
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
        new_mto = user.proxy_email
        response.replace_header('in-reply-to', "<%s>" % message.message_id)
        response.replace_header('references', "<%s>" % message.message_id)
        response.replace_header('to', "%s <%s>" % (message.message_id,
                                      new_mto))
        fp = StringIO(response.as_string()) 
        response = make_response_from_file(fp)
        self.assertTrue(response)
        
        # now parse in an email that isn't a response to anything
        fp = open("./testdata/mail2.txt", "r")
        response = make_response_from_file(fp)
        self.assertEqual(response, EX_NOUSER)
