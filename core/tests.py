from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

class TotalIssuesViewTest(TestCase):
    def setUp(self):
        #Create a test user
        self.user = User.objects.create_user(username='user_test', password='test123')
        self.user.save()

        #Define an example token
        self.token = 'fake-token'

        #Instantiate a Django client to simulate requests
        self.client = Client()

        #Save username and token in session
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = self.token
        session.save()

    @patch('requests.post')
    def test_total_issues_success(self, mock_post):
        #Mock GitHub API response for first open issue query
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 5}}}, 200),  #Total issues
        ]

        response = self.client.get(reverse('total_issues'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        self.assertEqual(response.json()['total_issues'], 5)

#Helper class to simulate GitHub response
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json