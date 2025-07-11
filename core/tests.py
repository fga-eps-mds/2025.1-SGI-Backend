from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from models import Profile
from unittest.mock import patch
#from views import blacklist 

class TestsGitFIca(APITestCase):
    
    #inciializacao e criação de sessao do usuario pra fazerr os testes
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser',password='testpass')
        self.user.save()

        self.session = self.client.session
        self.session['username'] = 'testuser'
        self.session['token'] = 'mocked_github_token'
        self.session.save()
        
     #teste para chamadas com sucesso a api do github 
    @patch('core.views.requests.post')
    def test_total_prs_closed(self, mock_post):
        
        #Mockando resposta da api pra poder fazer o teste da views
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': {
                'search': {
                    'issueCount': 5
                }
            }
        }
    
        #Conferindo se as saidas foram corretas
        response = self.client.get(f'/api/users/{self.user.id}/pull_request_fechados')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_pr'], 5)

    #teste para quando a api não consegue passar todos os dados necessarios
    @patch('core.views.requests.post')
    def test_total_prs_closed_data_error(self):
        #Fazer o request com dados faltando 
        session = self.client.session
        session.clear()
        session.save()

        response = self.client.get(f'/api/users/{self.user.id}/pull_request_fechados')
        self.assertEqual(response.status_code, 500)