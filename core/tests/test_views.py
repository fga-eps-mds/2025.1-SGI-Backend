from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import patch
from django.http import JsonResponse
from core.views import total_prs
import json


class MockResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


class GitHubAuthViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('core.views.requests.post')
    def test_total_prs_working(self, mock_post):
        # Testa se a view total_prs retorna corretamente o total de pull requests

        user = User.objects.create_user(username='testuser', password='123')

        # Mock da resposta da API do GitHub
        mock_post.return_value = MockResponse({
            "data": {
                "search": {
                    "issueCount": 4
                }
            }
        }, 200)

        # Cria request fake com sessão simulada
        request = self.factory.get(f'/api/users/{user.id}/pull_request')
        request.session = {
            'username': 'testuser',
            'token': 'fake_token'
        }

        response = total_prs(request)  # Chama diretamente a view
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('total_pr', data)
        self.assertEqual(data['total_pr'], 4)

    @patch('core.views.requests.post')
    def test_total_prs_user_not_found(self, mock_post):
        # Testa o comportamento quando o usuário não existe

        request = self.factory.get('/api/users/999/pull_request')
        request.session = {
            'username': 'usuario_inexistente',
            'token': 'fake_token'
        }

        with self.assertRaises(User.DoesNotExist):
            total_prs(request)

    def test_total_prs_missing_token(self):
        # Testa o comportamento quando não há token na sessão

        user = User.objects.create_user(username='testuser', password='123')
        request = self.factory.get(f'/api/users/{user.id}/pull_request')
        request.session = {
            'username': 'testuser'
            # absent token
        }

        with self.assertRaises(KeyError):
            total_prs(request)
