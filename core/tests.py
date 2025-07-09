from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
from views import blacklist 

class TestsGitFIca(APITestCase):
    
    #inicialização e configuração base pros testes do django test
    def setUp(self):
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
        