from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from django.urls import reverse
from .models import Profile  
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from .views import blacklist

# Constantes para testes
def get_test_credentials():
    """Returns test credentials for user creation"""
    return {
        'pwd': 'test_password_123!',  # NOSONAR - Test credential only
        'username': 'test_user',
        'email': 'test@example.com'
    }

TEST_CREDENTIALS = get_test_credentials()
TEST_PASSWORD = TEST_CREDENTIALS['pwd']  # NOSONAR - Test credential only
TEST_USERNAME = TEST_CREDENTIALS['username']
TEST_EMAIL = TEST_CREDENTIALS['email'] 

class TotalIssuesViewTest(TestCase):
    def setUp(self):
        #Create a test user
        self.user = User.objects.create_user(username='user_test', password='test123')
        self.user.save()

        #Define an example token
        self.token = 'fake-token'

        #Instantiate a Django client to simulate requests
        self.client = Client()

        #Save username and token in session
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = self.token
        session.save()

    @patch('requests.post')
    def test_total_issues_success(self, mock_post):
        #Mock GitHub API response for first open issue query
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 5}}}, 200),  #Total issues
        ]

        response = self.client.get(reverse('total_issues'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        self.assertEqual(response.json()['total_issues'], 5)

#Helper class to simulate GitHub response
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

class TestsGitFIca(TestCase):
    
    def setUp(self):
        self.cliente = Client()
        self.usuario = User.objects.create_user(
            username='usuario_teste', 
            password=TEST_PASSWORD
        )
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

        #verificação se foi salvo na models 
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.pontos_prs_approved, 50)
    #teste para quando a api não consegue passar todos os dados necessarios
    @patch('core.views.requests.post')
    def test_total_prs_closed_data_error(self):
        #Fazer o request com dados faltando 
        session = self.client.session
        session.clear()
        session.save()

        response = self.client.get(f'/api/users/{self.user.id}/pull_request_fechados')
        self.assertEqual(response.status_code, 500)
        
    @patch('core.views.requests.post')
    def test_total_prs(self, mock_post):
        response = self.client.get(f'/api/users/{self.user.id}/pull_request')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_pr'], 5)

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.pontos_prs_abertos, 50)
        
    #teste para quando a api não consegue passar todos os dados necessarios
    @patch('core.views.requests.post')
    def test_total_prs_data_error(self):
        response = self.client.get(f'/api/users/{self.user.id}/pull_request')
        self.assertEqual(response.status_code, 500)

class TotalIssuesViewTest(TestCase):
    def setUp(self):
        #Create a test user
        self.user = User.objects.create_user(
            username='user_test', 
            password=TEST_PASSWORD
        )
        self.user.save()

        #Creates an associated profile if the view's get_or_create needs it
        Profile.objects.create(user=self.user)

        #Define an example token
        self.token = 'fake-token'

        #Instantiate a Django client to simulate requests
        self.client = Client()

        #Save username and token in session
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = self.token
        session.save()

    @patch('requests.post')
    def test_total_issues_success(self, mock_post):
        #Mock GitHub API response for first open issue query
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 5}}}, 200),  #Total issues
            MockResponse({'data': {'search': {'issueCount': 3}}}, 200),  #Closed issues 
        ]

        response = self.client.get(reverse('total_issues'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        self.assertEqual(response.json()['total_issues'], 5)
        self.assertEqual(response.json()['total_issues_closed'], 3)
        self.assertEqual(response.json()['pontuação_issues'], 30)


#Helper class to simulate GitHub response
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    
class ProfileModelTest(TestCase):
    def test_create_profile_with_default_score(self):
        #Create a test user
        user = User.objects.create_user(
            username='user_test', 
            password=TEST_PASSWORD
        )

        #Create a related Profile
        profile = Profile.objects.create(user=user)

        #Tests if the Profile was created correctly
        self.assertEqual(profile.user.username, 'user_test')

        #Checks if the score starts with 0
        self.assertEqual(profile.pontuacao_issues, 0)

    def test_update_pontuacao_issues(self):
        user = User.objects.create_user(
            username='user_test2', 
            password=TEST_PASSWORD
        )
        profile = Profile.objects.create(user=user)

        #Update the score
        profile.pontuacao_issues = 50
        profile.save()

        #Recover again and test
        updated = Profile.objects.get(user=user)
        self.assertEqual(updated.pontuacao_issues, 50)


class TestsGitFIca(APITestCase):
    
    #inicialização e configuração base pros testes do django test
    def setUp(self):

        
        self.client = APIClient()
        #criação do user pra testar o view profile 
        self.user = User.objects.create_user(
            username='teste',
            password=TEST_PASSWORD,
            first_name='Test',
            email=TEST_EMAIL
        )
        # tem que criar o profile emulado ja que essas info não estã ocontidas no user do django
        self.profile = Profile.objects.create(
            user=self.user,
            avatar='',
            bio='teste'
        )
        self.refresh = RefreshToken.for_user(self.user)
    
    #teste pra solicitaçao sem ter o usuario autenticado no programa 
    def test_user_profile_no_auutentication(self):
        response = self.client.get('/api/users/me/')  
        self.assertEqual(response.status_code, 401)
    
    #teste para usuario autenticado 
    def test_get_user_profile_autenticated(self):
        # simulando autenticação do usuario
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')
        
        response = self.client.get('/api/users/me/') 
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['nome'], 'Test')
        self.assertEqual(data['username'], 'teste')
        self.assertEqual(data['email'], TEST_EMAIL)
        self.assertEqual(data['avatar'], '')
        self.assertEqual(data['bio'], 'teste')


        self.user = User.objects.create_user(
            username='usuarioteste123', 
            password=TEST_PASSWORD,
            email=TEST_EMAIL
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client = APIClient()
        
    #teste para metodos diferentes do delete
    def test_deleteuser_method_error(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')
        response = self.client.get('/DELETE/api/users/me/') 
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['error'], 'Method not allowed')
        
    #teste para chamadas sem nenhum token
    def test_deleteuser_no_token(self):
        response = self.client.delete('/DELETE/api/users/me/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Authorization token required')
    
    #Teste pra chamadas com token mas token inválido
    def test_deleteuser_token_error(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer testeinvalidd')
        response = self.client.delete('/DELETE/api/users/me/')
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid', response.json()['error'])
        
    #teste para chamadas com token válido 
    def test_delete_user_with_valid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')
        response = self.client.delete('/DELETE/api/users/me/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(User.objects.filter(username='testuser').exists(), False)

    

        self.user = User.objects.create_user(
            username='usuarioteste123', 
            password=TEST_PASSWORD
        )
        self.client = APIClient()
    
    #teste pra quando o blacklist recebe um gwt invalido
    def test_blacklist_false_token(self):
        invalid_token = 'testetesteteste'
        result = blacklist(None, invalid_token)
        self.assertFalse(result)
        
    #teste pra jwt valido 
    def test_blacklist_token_correct(self):
        testJwt = RefreshToken.for_user(self.user) #Essa função vai emular um jwt válido pra testar se o blacklist ta funcionando certinho 
        result = blacklist(None, str(testJwt))
        self.assertTrue(result)
    
    #Teste para qualquer tipo de metodo que não seja o post que foi definido la no logout     
    def test_logout_methoderror(self):
        response = self.client.get('/api/auth/logout')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['success'], False)
        
    #teste para quando da o erro token not provided la no logout 
    def test_logout_token_error(self):
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        
    #teste pra quando é enviado um gwt invalido pro logout 
    def test_logout_token_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer tokeninvalidotesteteste')
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        
    #teste pra token valido no logout 
    def test_logout_token_correct(self):
        testJwt = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(testJwt)}')

        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(response.json()['message'], 'Logout successful')


