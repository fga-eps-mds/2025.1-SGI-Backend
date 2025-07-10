from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse
from django.http import JsonResponse

class TestsGitFIca(TestCase):
    
    #testes para quando a api do github da erro 
    @patch('core.views.requests.get')
    def test_github_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 500

        response = self.client.get('/api/users/teste/')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error'], 'Error accessing GitHub')
        
    #testes para quando api funciona corretamente mas não econtra nenhum usuario publico 
    @patch('core.views.requests.get')
    def test_github_user_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404

        response = self.client.get('/api/users/teste/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'User not found')
        
    #teste para quando a api é chamada e encontra um usuario
    @patch('core.views.requests.get')
    def test_github_user_found(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'userteste',
            'avatar_url': './avatar.png',
            'bio': 'teste'
        }

        response = self.client.get('/api/users/userteste/')  # username simulado
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'userteste')
        self.assertEqual(data['avatar_url'], './avatar.png')
        self.assertEqual(data['bio'], 'teste')
