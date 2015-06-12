
from django.test import TestCase
from django.contrib.auth.models import User

from model_mommy import mommy

from ahem.backends import BaseBackend
from ahem.notification import Notification
from ahem.scopes import QuerySetScope, ContextFilterScope


class TestBackend(BaseBackend):
    name = 'test_backend'
    required_settings = ['username', 'id']


class TestBackend(BaseBackend):
    name = 'other_backend'


class QuerySetNotification(Notification):
    name = 'query_set_notification'
    backends = ['test_backend', 'other_backend']

    scope = QuerySetScope()

    templates = {
        'default': 'ahem/tests/test_template.html'}


class CustomQuerySetNotification(Notification):
    name = 'custom_query_set_notification'
    backends = ['test_backend', 'other_backend']

    scope = QuerySetScope(User.objects.filter(is_staff=True))

    templates = {
        'default': 'ahem/tests/test_template.html'}


class QuerySetScopeTests(TestCase):

    def setUp(self):
        self.users = mommy.make('auth.User', _quantity=3)

    def test_gets_all_users_if_no_query_scope_is_set(self):
        users = self.users
        notification = QuerySetNotification()

        notification_users = notification.get_users({})
        self.assertEqual(len(users), len(notification_users))

    def test_a_queryset_can_be_passed_to_the_scope(self):
        staffs = mommy.make('auth.User', is_staff=True, _quantity=2)

        notification = CustomQuerySetNotification()

        notification_users = notification.get_users({})
        self.assertEqual(len(staffs), len(notification_users))
