from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
#from views import blacklist 
#from models import Profile

class TestsGitFIca(APITestCase):
    
    #inicialização e configuração base pros testes do django test
    def setUp(self):
        self.user = User.objects.create_user(username='usuarioteste123', password='testeteste123',email='test@teste.com')
        self.refresh = RefreshToken.for_user(self.user)
        self.client = APIClient()