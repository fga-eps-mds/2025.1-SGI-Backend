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

        response = self.client.get('/api/users/octocat/')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error'], 'Error accessing GitHub')