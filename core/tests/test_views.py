from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import patch
from datetime import datetime, timezone as dt_timezone
from core.views import total_points_stats
import json

class TotalPointsStatsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='user', email='user@example.com')
        self.user.date_joined = datetime(2024, 6, 15, tzinfo=dt_timezone.utc)
        self.user.save()

    @patch('core.views.requests.post')
    def test_total_points_stats_success(self, mock_post):
        # Função que retorna respostas diferentes com base na query
        def mocked_post(url, json, headers):
            query = json['query']

            if "totalCommitContributions" in query:
                return MockResponse({
                    "data": {
                        "viewer": {
                            "contributionsCollection": {
                                "totalCommitContributions": 3
                            }
                        }
                    }
                })
            elif "type:issue" in query:
                return MockResponse({
                    "data": {
                        "search": {
                            "issueCount": 2
                        }
                    }
                })
            elif 'is:pr is:open' in query and 'review:approved' not in query:
                return MockResponse({
                    "data": {
                        "search": {
                            "issueCount": 1
                        }
                    }
                })
            elif 'review:approved' in query:
                return MockResponse({
                    "data": {
                        "search": {
                            "issueCount": 4
                        }
                    }
                })
            elif 'is:pr is:merged' in query:
                return MockResponse({
                    "data": {
                        "search": {
                            "issueCount": 5
                        }
                    }
                })

            return MockResponse({})  # fallback

        mock_post.side_effect = mocked_post

        request = self.factory.get('/fake-url')
        request.session = {
            'username': 'user',
            'token': 'fake_token'
        }

        response = total_points_stats(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data['username'], 'user')
        self.assertIn('points_y/m', data)

        key = self.user.date_joined.strftime('%Y-%m')
        self.assertIn(key, data['points_y/m'])

        # Esperado: (3 + 2 + 1 + 4 + 5) * 10 = 150
        self.assertEqual(data['points_y/m'][key], 150)


# Classe auxiliar para simular respostas da API
class MockResponse:
    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json
