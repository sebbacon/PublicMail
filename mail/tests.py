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
from mail.forms import MailForm
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
        mail1 = Mail.objects.create(
            subject="ho",
            mfrom=user,
            mto=user,
            message="for the life of a bear")
        
        mail2 = Mail.objects.create(
            subject="tiddly pom",
            mfrom=user,
            mto=user,
            message="it goes on snowing",
            in_reply_to=mail1)
        mail1.save()
        mail2.save()
        c = Client()
        self.assertEqual(mail1.childwalk().next(), mail2)
        response = c.get(reverse('mail',
                                 kwargs={'mail':mail1.pk}))
        self.assertContains(response, "tiddly pom")
        response = c.get(reverse('mail',
                                 kwargs={'mail':mail2.pk}),
                         follow=True)
        self.assertContains(response, "life of a bear")
        
    def testPreview(self):
        user = CustomUser.objects.create(email="admin@baz.com",
                                         username="admin@baz.com",
                                         needs_moderation=False)
        user.set_unusable_password()
        mail1 = Mail.objects.create(
            subject="ho",
            mfrom=user,
            mto=user,
            message="for the life of a bear")
        # first, make sure we can only preview mails that have been
        # approved (by following link from email)
        c = Client()
        c.login(mail=mail1)
        url = reverse('preview',
                      kwargs={'mail':mail1.pk})
        response = c.get(url, follow=True)
        self.assertContains(response, "not been approved")
        mail1.approved = True
        mail1.save()
        response = c.get(url, follow=True)
        self.assertContains(response, "bin it")
        preview_data = {'post':True}
        # users without passwords are asked to set up their account
        response = c.post(url, preview_data, follow=True)
        self.assertTemplateUsed(response,
                                'login_or_register_form.html')
        mail1 = Mail.objects.get()
        self.assertTrue(mail1.previewed)
        # users without passwords just get the standard mail page
        user.set_password("password")
        user.save()
        response = c.post(url, preview_data, follow=True)
        self.assertTemplateUsed(response,
                                'view_mail_thread.html')
        # check deleting
        preview_data = {'delete':True}
        response = c.post(url, preview_data, follow=True)
        self.assertEqual(Mail.objects.all().count(), 0)
        
        

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
        form = MailForm(None, data)
        self.assertFalse(form.is_valid())
        data.update({'mto':'1@baz.com',
                     'mfrom':user.email,
                     'subject':SUBJECT,
                     'name': 'One Baz',
                     'message':'Hi'})
        form = MailForm(None, data)
        self.assertTrue(form.is_valid())
        
        mail_obj = form.save()
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
        # this was like a different person at the same company
        # replying to the message -- let's check that while we're here
        couser1 = CustomUser.objects.get(email='1@baz.com')
        couser2 = CustomUser.objects.get(email='11@baz.com')
        self.assertEqual(couser1.organisation, couser2.organisation)

        # two emails should have been created, threaded together
        mails = Mail.objects.order_by('created')
        self.assertEqual(mails[0].childwalk().next(), mails[1])
        # and an email should have been sent to the original sender,
        # with a proxied reply-to address
        self.assertEqual(mail.outbox[-1].to[0],
                         user.email)
        self.assertEqual(mail.outbox[-1].from_email,
                         couser2.email)
        self.assertEqual(mail.outbox[-1].extra_headers['Reply-To'],
                         couser2.proxy_email)

    def testCustomUserModelProxy(self):
        user = CustomUser.objects.create(email="bar@baz.com",
                                         username="bar@baz.com")
        self.assertNotEqual(user.proxy_email, None)

    def testSimpleMailForm(self):
        data = QueryDict("").copy()
        data.update({'mto':'1@baz.com',
                     'mfrom':'2@baz.com',
                     'subject':'Hello',
                     'name':'Two Baz',
                     'message':'Hi'})
        form = MailForm(None, data)
        self.assertTrue(form.is_valid())
        mail = form.save()
        self.assertEquals(mail.mto.email, data['mto'])
        self.assertEquals(mail.mfrom.email, data['mfrom'])

        # sending the same message twice is OK
        data.update({'mto':'1@baz.com',
                     'mfrom':'2@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MailForm(None, data)
        self.assertTrue(form.is_valid())
        mail = form.save()
        self.assertFalse(mail.approved)
        
        # now try with a userfo who's unmoderated
        user = CustomUser.objects.create(email="3@baz.com",
                                         username="3@baz.com",
                                         needs_moderation=False)
        data.update({'mto':'1@baz.com',
                     'mfrom':'3@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MailForm(None, data)
        self.assertTrue(form.is_valid())
        mail = form.save()
        self.assertTrue(mail.approved)

    def testSignupWorkflow(self):
        write_data = {'mto':'4@baz.com',
                'mfrom':'5@baz.com',
                'subject':'Hello',
                'name':'Five Baz',
                'message':'Hi'}
        
        c = Client()
        # first time they visit, they should get to the register form
        response = c.post(reverse('write'), write_data, follow=True)
        self.assertContains(response, "check your inbox")
        mail = Mail.objects.get()
        reg_data = {'email':mail.mfrom.email,
                    'password':'asd',
                    'repeat_password':'asd'}
        response = c.post(reverse('login_or_register_form',
                                  kwargs={'mail':\
                                          mail.id}),
                          reg_data,
                          follow=True)

        self.assertContains(response, 'Your conversations')
        # test logging out
        response = c.get('/logout', follow=True)
        self.assertNotContains(response, 'Your conversations')
        
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
        self.assertContains(response, 'Your conversations')
        
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
        mail = Mail.objects.create(
            subject=message['subject'],
            mfrom=user,
            mto=recipient,
            message=body)

        # now we simulate a reply, and override a couple of relevant
        # headers 
        raw_email = email.message_from_file(
            open("./testdata/mail4.txt", "r"))
        new_mto = user.proxy_email
        raw_email.replace_header('in-reply-to', "<%s>" % mail.message_id)
        raw_email.replace_header('references', "<%s>" % mail.message_id)
        raw_email.replace_header('to', "%s <%s>" % (mail.message_id,
                                      new_mto))
        fp = StringIO(raw_email.as_string()) 
        response = make_response_from_file(fp)
        self.assertTrue(response)
        
        # now parse in an email that isn't a response to anything
        fp = open("./testdata/mail2.txt", "r")
        response = make_response_from_file(fp)
        self.assertEqual(response, EX_NOUSER)

        # and now try threading based on subject line as a fallback...
        raw_email = email.message_from_file(
            open("./testdata/mail2.txt", "r"))
        new_mto = user.proxy_email
        del(raw_email['in-reply-to'])
        del(raw_email['references'])
        raw_email.replace_header('subject', "Re:RE: re:%s" % mail.subject)
        raw_email.replace_header('to', "%s <%s>" % (mail.message_id,
                                      new_mto))
        fp = StringIO(raw_email.as_string()) 
        response = make_response_from_file(fp)
        self.assertTrue(response)
