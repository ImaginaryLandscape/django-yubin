import logging
from io import StringIO
import unittest

from django.conf import settings as django_settings
from django.core import mail
from django.utils.encoding import force_text

from django_yubin import engine, settings, models, constants, queue_email_message

from .base import MailerTestCase


@unittest.skip("TODO: Reimplement")
class SendMessageTest(MailerTestCase):
    """
    Tests engine functions that send messages.
    """

    def setUp(self):
        # Set EMAIL_BACKEND
        super(SendMessageTest, self).setUp()
        if hasattr(django_settings, 'EMAIL_BACKEND'):
            self.old_email_backend = django_settings.EMAIL_BACKEND
        else:
            self.old_email_backend = None
        django_settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.' \
                                        'EmailBackend'

        # Create somewhere to store the log debug output.
        self.output = StringIO()

        # Create a log handler which can capture the log debug output.
        self.handler = logging.StreamHandler(self.output)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(formatter)

        # Add the log handler.
        logger = logging.getLogger('django_yubin')
        logger.addHandler(self.handler)

    def tearDown(self):
        # Restore EMAIL_BACKEND
        super(SendMessageTest, self).tearDown()
        if self.old_email_backend:
            django_settings.EMAIL_BACKEND = self.old_email_backend
        else:
            delattr(django_settings, 'EMAIL_BACKEND')

        # Remove the log handler.
        logger = logging.getLogger('django_yubin')
        logger.removeHandler(self.handler)

    def testUnicodeErrorQueuedMessage(self):
        """
        Checks that we capture unicode errors on mail
        """
        from django.core.management import call_command
        msg = mail.EmailMessage(subject='subject', body='body',
                                from_email=u'juan.lópez@abc.com', to=['mail_to@abc.com'])
        msg.send()
        queued_messages = models.QueuedMessage.objects.all()
        self.assertEqual(queued_messages.count(), 1)
        call_command('send_mail', verbosity='0')
        num_errors = models.Log.objects.filter(result=constants.RESULT_FAILED).count()
        self.assertEqual(num_errors, 1)

    def testUnicodeQueuedMessage(self):
        """
        Checks that we capture unicode errors on mail
        """
        from django.core.management import call_command
        msg = mail.EmailMessage(subject=u'Chère maman',
                                body='Je t\'aime très fort',
                                from_email='mail_from@abc.com',
                                to=['to@example.com'])
        msg.send()

        queued_messages = models.QueuedMessage.objects.all()
        self.assertEqual(queued_messages.count(), 1)

        call_command('send_mail', verbosity='0')

        queued_messages = models.QueuedMessage.objects.all()
        self.assertEqual(queued_messages.count(), 0)

        num_errors = models.Log.objects.filter(result=constants.RESULT_FAILED).count()
        self.assertEqual(num_errors, 0)

        message = msg.message()
        self.assertEqual(message['subject'], '=?utf-8?q?Ch=C3=A8re_maman?=')
        self.assertEqual(force_text(message.get_payload()), 'Je t\'aime très fort')

    def test_send_queued_message(self):
        self.queue_message()
        self.assertEqual(models.QueuedMessage.objects.count(), 1)
        q_message = models.QueuedMessage.objects.first()
        result = engine.send_queued_message(q_message)
        self.assertEqual(result, constants.RESULT_SENT)

    def test_pause_queued_message(self):
        self.queue_message()
        self.assertEqual(models.QueuedMessage.objects.count(), 1)
        q_message = models.QueuedMessage.objects.first()
        _original, settings.PAUSE_SEND = settings.PAUSE_SEND, True
        result = engine.send_queued_message(q_message)
        settings.PAUSE_SEND = _original
        self.assertEqual(result, constants.RESULT_SKIPPED)

    def test_send_message(self):
        email_message = mail.EmailMessage('subject', 'body', 'from@email.com',
                                          ['to@email.com'])
        result = engine.send_message(email_message)
        self.assertEqual(result, constants.RESULT_SENT)

    def test_pause_send_message(self):
        email_message = mail.EmailMessage('subject', 'body', 'from@email.com',
                                          ['to@email.com'])
        _original, settings.PAUSE_SEND = settings.PAUSE_SEND, True
        result = engine.send_message(email_message)
        settings.PAUSE_SEND = _original
        self.assertEqual(result, constants.RESULT_SKIPPED)

    def test_send_all_non_empty_queue(self):
        msg = mail.EmailMessage('subject', 'body', 'from@email.com',
                                ['to@email.com'])
        queue_email_message(msg)
        engine.send_all()
        self.output.seek(0)
        self.assertEqual(self.output.readlines()[-1].strip()[-8:], 'seconds.')

    def test_send_all_empty_queue(self):
        engine.send_all()
        self.output.seek(0)
        self.assertEqual(self.output.readlines()[2].strip(),
                         'No messages in queue.')
