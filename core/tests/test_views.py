from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from core.models import Profile
import json

# Auxiliary class to simulate http responses
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

class GitHubAuthViewTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_git_auth_code_redirects(self):
        with self.settings(GITHUB_CLIENT_ID='abc123', GITHUB_REDIRECT_URI='http://localhost/callback'):
            response = self.client.get('/api/auth/github')
            self.assertEqual(response.status_code, 302)
            self.assertIn('https://github.com/login/oauth/authorize', response.url)

    @patch('core.views.requests.post')
    @patch('core.views.requests.get')
    def test_git_auth_token_and_user_creation(self, mock_get, mock_post):
        # Mock POST for /access_token
        mock_post.return_value = MockResponse({'access_token': 'fake_token'}, 200)

        # Mock GET for /user and /emails
        mock_get.side_effect = [
            MockResponse({'login': 'user_github'}, 200),
            MockResponse([{'email': 'user@example.com', 'primary': True, 'verified': True}], 200)
        ]

        with self.settings(GITHUB_CLIENT_ID='abc', GITHUB_CLIENT_SECRET='def', GITHUB_REDIRECT_URI='http://localhost'):
            response = self.client.get('/callback?code=abc123')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data['username'], 'user_github')
            self.assertEqual(data['email'], 'user@example.com')
            self.assertTrue(User.objects.filter(username='user_github').exists())

    def test_git_auth_token_missing_code(self):
        response = self.client.get('/callback')  # Sem ?code=
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No code provided by GitHub')

    @patch('core.views.requests.post')
    def test_total_commits_calculation(self, mock_post):
        user = User.objects.create_user(username='user123', password='123')
        self.client.force_login(user)

        # Simulates session with token and username
        session = self.client.session
        session['username'] = 'user123'
        session['token'] = 'fake_token'
        session.save()

        # GRAPHQL response mock
        mock_post.return_value = MockResponse({
            "data": {
                "viewer": {
                    "contributionsCollection": {
                        "totalCommitContributions": 7
                    }
                }
            }
        }, 200)

        response = self.client.get('/api/users/id/total_commits')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['total_commits'], 7)
        self.assertEqual(data['pontuacao_commits'], 70)

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.pontuacao_commits, 70)
