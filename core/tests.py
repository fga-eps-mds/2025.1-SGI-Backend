from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch

class TesteTotalCommitsView(TestCase):
    
    def setUp(self):
        self.cliente = Client()
        self.usuario = User.objects.create_user(username='usuario_teste', password='senha123')
        self.usuario.date_joined = '2023-01-01T00:00:00Z'  
        self.usuario.save()

    @patch('core.views.requests.post')
    def test_total_commits_sucesso(self, requisicao_mockada):
        
        # simulando resposta da api git
        requisicao_mockada.return_value.status_code = 200
        
        requisicao_mockada.return_value.json.return_value = {
            "data": {
                "viewer": {
                    "contributionsCollection": {
                        "totalCommitContributions": 42
                    }
                }
            }
        }

        # simulando sessão do usuario
        sessao = self.cliente.session
        sessao['username'] = 'usuario_teste'
        sessao['token'] = 'token_falso'
        sessao.save()

        #Chamando o método para testar
        resposta = self.cliente.get('/api/users/id/total_commits')

        #Verificando a resposta
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {
            'usuario': 'usuario_teste',
            'total_commits': 42
        })

    @patch('core.views.requests.post')
    def test_total_commits_erro_github(self, requisicao_mockada):
        #simulando teste erro
        requisicao_mockada.return_value.status_code = 500

        sessao = self.cliente.session
        sessao['username'] = 'usuario_teste'
        sessao['token'] = 'token_falso'
        sessao.save()

        resposta = self.cliente.get('/api/users/id/total_commits')

        self.assertEqual(resposta.status_code, 500)
        self.assertIn('error', resposta.json())
        self.assertEqual(resposta.json()['error'], 'Error GraphQL')
