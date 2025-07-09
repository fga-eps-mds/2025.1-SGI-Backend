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
        
    def blacklist_false_token(self):
        invalid_token = 'testetesteteste'
        result = blacklist(None, invalid_token)
        self.assertFalse(result)