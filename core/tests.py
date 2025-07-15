from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
#from models import Profile
from views import blacklist 

class TestsGitFIca(APITestCase):
    
    #inicialização e configuração base pros testes do django test
    def setUp(self):

        self.user = User.objects.create_user(username='usuarioteste123', password='testeteste123',email='test@teste.com')
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

    

        self.user = User.objects.create_user(username='usuarioteste123', password='testeteste123')
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

