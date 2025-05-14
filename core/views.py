from django.shortcuts import render, redirect 
#from .models import user 
from . import settings


def api_auth_git(request):
    gitCode = request.GET.get('code')
    request.post(f"https://github.com/login/oauth/access_token?client_id={settings.GITHUB_CLIENT_ID}&client_secret{settings.GITHUB_CLIENT_SECRET}&code={gitCode}&redirect_uri=http://localhost:8000/api/auth/github")

    acessToken_recieved = request.post(
    "https://github.com/login/oauth/access_token",
    data={

        #parametros que o github exige para conseguirmos o token 
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_CLIENT_SECRET,
        'code': gitCode,
        'redirect_uri': 'http://localhost:8000/api/auth/github',
    },
    headers={'Accept': 'application/json'}
)
    token_data = acessToken_recieved.json()
    access_token = token_data.get('access_token')
    #access_token pega o token do git

    #precisa retornar um JWT agora depois que autentiar o token

def login(request):
    github_auth_url = ("https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri=http://localhost:8000/api/auth/github")
    return redirect(github_auth_url)
    #redireciona para o GitHUb depois redireciona para a pagina de login

def index():
    pass