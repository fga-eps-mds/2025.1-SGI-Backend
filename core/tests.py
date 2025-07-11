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