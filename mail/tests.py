import unittest
from django.test import TestCase
from django.http import QueryDict
from django.test.client import Client

from mail.models import Recipient
from mail.models import CustomUser
from mail.forms import MessageForm

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
        form = MessageForm(data)
        self.assertTrue(form.is_valid())
        message = form.save()
        self.assertEquals(message.mto.email, data['mto'])
        self.assertEquals(message.mfrom.email, data['mfrom'])

        # sending the same message twice is OK
        data.update({'mto':'1@baz.com',
                     'mfrom':'2@baz.com',
                     'subject':'Hello',
                     'message':'Hi'})
        form = MessageForm(data)
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
        form = MessageForm(data)
        self.assertTrue(form.is_valid())
        message = form.save()
        self.assertTrue(message.approved)

    def testSignupWorkflow(self):
        data = {'mto':'4@baz.com',
                'mfrom':'5@baz.com',
                'subject':'Hello',
                'message':'Hi'}
        
        c = Client()
        response = c.post('/', data, follow=True)
        self.assertContains(response, "Repeat password")

        data = {'email':response.context['message'].mfrom.email,
                'password':'asd',
                'repeat_password':'asd'}

        response = c.post(response.request['PATH_INFO'],
                          data,
                          follow=True)
        self.assertTemplateUsed(response, 'preview.html')
        
        
