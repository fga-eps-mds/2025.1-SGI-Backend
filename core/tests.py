from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from django.utils import timezone
import datetime

#Mock GitHub API Response
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

class IssuesMonthsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        #Creates a user with a registration date in May
        self.user = User.objects.create_user(username='user_test', password='123456')
        self.user.date_joined = datetime.datetime(2025, 5, 10, tzinfo=datetime.timezone.utc)
        self.user.save()

        #Set token and username in the session
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = 'fake-token'
        session.save()

    @patch('requests.post')
    def test_issues_months(self, mock_post):
        #Simulates 3-month-old GitHub API responses
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 2}}}),  #May
            MockResponse({'data': {'search': {'issueCount': 5}}}),  #June
            MockResponse({'data': {'search': {'issueCount': 1}}}),  #July
        ]

        #Run the view
        response = self.client.get(reverse('issues_months'))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['username'], 'user_test')
        self.assertIn('2025', data['issues_y/m'])
        self.assertEqual(data['issues_y/m']['2025']['05'], 2)
        self.assertEqual(data['issues_y/m']['2025']['06'], 5)
        self.assertEqual(data['issues_y/m']['2025']['07'], 1)
