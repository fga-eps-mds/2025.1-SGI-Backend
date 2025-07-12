from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from django.utils import timezone
import datetime

#Mock response for requests.post
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

class TotalPRsStatsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user_test', password='1234')
        #Assume the user joined in May 2025
        self.user.date_joined = datetime.datetime(2025, 5, 10, tzinfo=datetime.timezone.utc)
        self.user.save()

        #Configure the session with username and token
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = 'fake-token'
        session.save()

    @patch('requests.post')
    def test_total_prs_stats(self, mock_post):
        #Mock 3 consecutive months: May, June, July
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 1}}}),  #May
            MockResponse({'data': {'search': {'issueCount': 2}}}),  #June
            MockResponse({'data': {'search': {'issueCount': 3}}}),  #July
        ]

        response = self.client.get(reverse('total_prs_stats'))
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['username'], 'user_test')
        self.assertIn('2025', data['open_prs_y/m'])
        self.assertEqual(data['open_prs_y/m']['2025']['05'], 1)
        self.assertEqual(data['open_prs_y/m']['2025']['06'], 2)
        self.assertEqual(data['open_prs_y/m']['2025']['07'], 3)