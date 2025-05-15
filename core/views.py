from django.shortcuts import render, redirect 
#from .models import user 
from . import settings
import requests


def git_auth_token(request):

    gitCode = request.GET.get('code')
    
    requestCodeToken = request.post(
    "https://github.com/login/oauth/access_token",
    data={

        #parametros que o github exige para conseguirmos o token 
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_CLIENT_SECRET,
        'code': gitCode,
        'redirect_uri': 'http://localhost:8000/api/auth/github/',
    },
    headers={'Accept': 'application/json'}
)
    
    infosJson = requestCodeToken.json()
    tokenNumber = infosJson.get('access_token') # aqui encerra o segundo topico da US01 

    """" topico 3 US01 
    user_response = request.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()
    #pega o nome do usuario

    email_response = request.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()
    #pega o email do usuraio

    #precisa retornar um JWT agora depois que autentiar o token
    
    """

def git_auth_code(request):
    request.get = ("https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri=http://localhost:8000/api/auth/token")
    redirect(git_auth_token)

def index():
    pass