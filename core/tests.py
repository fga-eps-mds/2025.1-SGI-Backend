from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

#Mock for GitHub mock response
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

class TotalMergesViewTest(TestCase):
    def setUp(self):
        #Create user
        self.user = User.objects.create_user(username='user_test', password='1234')
        self.token = 'fake-token'
        self.client = Client()

        #Save session with username and token
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = self.token
        session.save()

    @patch('requests.post')
    def test_total_merges_success(self, mock_post):
        #Simulates GitHub API response
        mock_post.return_value = MockResponse({
            'data': {
                'search': {
                    'issueCount': 4
                }
            }
        }, 200)

        response = self.client.get(reverse('total_merges'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_merges'], 4)