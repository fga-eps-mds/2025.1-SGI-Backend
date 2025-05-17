from django.shortcuts import render, redirect 
from . import settings

#verificar incompatibildiade
import requests

#página inicial de teste 
def index(request):
    return render(request, 'teste.html')

#recebe o code do github,troca por um access token e chama create_user
def git_auth_token(request):

    gitCode = request.GET.get('code')
    
    token_response = requests.post(
    "https://github.com/login/oauth/access_token",
    data={
        #parametros que o github exige para conseguirmos o token 
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_CLIENT_SECRET,
        'code': gitCode,
        'redirect_uri': 'http://localhost:8000/api/auth/token',
    },
    headers={'Accept': 'application/json'}
)
    
    token_data = token_response.json()
    access_token = token_data.get('access_token') # aqui encerra o segundo topico da US01 
    return create_user(request, access_token)
    
#redireciona o usuário para o github para autorizar o app 
def git_auth_code(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/api/auth/token"
    )
    return redirect(github_auth_url)

def create_user(request, access_token):
    #topico 3 US01 
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()
    #pega o nome do usuario

    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()
    #pega o email do usuraio

    #precisa retornar um JWT agora depois que autentiar o token
    
