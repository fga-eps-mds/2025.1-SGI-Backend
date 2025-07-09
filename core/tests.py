from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
#from views import blacklist 
from models import Profile

class TestsGitFIca(APITestCase):
    
    #inicialização e configuração base pros testes do django test
    def setUp(self):
        
        self.client = APIClient()
        #criação do user pra testar o view profile 
        self.user = User.objects.create_user(
            username='teste',
            password='teste',
            first_name='Test',
            email='test@teste.com'
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
