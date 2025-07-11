from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.http import JsonResponse
from unittest.mock import patch
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from core.views import approved_prs_stats
import json

class ApprovedPRsStatsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='user', email='user@example.com')
        self.user.date_joined = datetime(2024, 6, 15, tzinfo=dt_timezone.utc)
        self.user.save()

    @patch('core.views.requests.post')
    def test_approved_prs_stats_success(self, mock_post):
        mock_post.return_value.json.return_value = {
            "data": {
                "search": {
                    "issueCount": 3
                }
            }
        }

        request = self.factory.get('/fake-url')
        request.session = {
            'username': 'user',
            'token': 'fake_token'
        }

        response = approved_prs_stats(request)

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        self.assertEqual(json_data['username'], 'user')
        self.assertIn('approved_prs_y/m', json_data)

        year = self.user.date_joined.strftime('%Y')
        month = self.user.date_joined.strftime('%m')

        self.assertIn(year, json_data['approved_prs_y/m'])
        self.assertIn(month, json_data['approved_prs_y/m'][year])
        self.assertEqual(json_data['approved_prs_y/m'][year][month], 3)
