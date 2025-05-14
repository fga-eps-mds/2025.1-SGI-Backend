from django.shortcuts import render, redirect 
#from .models import user 
from . import settings


def api_auth_git(request):
    gitCode = request.GET.get('code')
    request.post(f"https://github.com/login/oauth/access_token?client_id={settings.GITHUB_CLIENT_ID}&client_secret{settings.GITHUB_CLIENT_SECRET}&code={gitCode}&redirect_uri=http://localhost:8000/api/auth/github")

    #precisa retornar um JWT agora depois que autentiar o token

def login(request):
    request.get(f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri=http://localhost:8000/api/auth/github")
    
def index():
    pass