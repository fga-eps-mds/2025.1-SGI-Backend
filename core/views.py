from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone

# Redireciona o usuário para o GitHub para autorizar o acesso
def git_auth_code(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    # Redireciona para a página de login/autorização do GitHub
    return redirect(github_auth_url)

# Recebe o "code" do GitHub e o troca por um token de acesso
def git_auth_token(request):
    # Obtém o código retornado pelo GitHub
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'No code provided by GitHub'}, status=400)

    # Envia uma requisição para o GitHub para trocar o código por um token de acesso
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
        },
        headers={'Accept': 'application/json'}
    )
    
    # Obtém o token de acesso da resposta
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    request.session['token'] = access_token
    if not access_token:
        return JsonResponse({'error': 'Failed to obtain access token from GitHub'}, status=400)

    # Chama a função que cria o usuário com base no token de acesso
    return create_user(request, access_token)

# Usa o token do GitHub para obter os dados do usuário e criar/fazer login no Django
def create_user(request, access_token):
    # Obtém dados básicos do usuário (como login, nome, etc.)
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()

    # Obtém a lista de e-mails do usuário
    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()

    # Tenta encontrar o e-mail primário e verificado
    username = user_data.get('login')
    request.session['username'] = username
    email = None
    for e in emails:
        if e.get('primary') and e.get('verified'):
            email = e.get('email')
            break

    if not email:
        return JsonResponse({'error': 'No verified primary email found in GitHub account'}, status=400)

    # Cria o usuário local (se ainda não existir) ou busca o existente
    date = timezone.now()
    user, created = User.objects.get_or_create(username=username, defaults={'email': email,'date_joined': date})

    # Gera tokens JWT para o usuário (login sem senha!)
    refresh = RefreshToken.for_user(user)
    access_jwt = str(refresh.access_token)
    refresh_jwt = str(refresh)

    # Retorna os dados do usuário e os tokens (se desejado, os tokens também podem ser incluídos)
    return JsonResponse({
        'username': username,
        'email': email,
    })


import requests
from django.http import JsonResponse

def total_commits(request):
    username = request.session.get('username')
    token = request.session.get('token')
    user = User.objects.get(username=username)
    date = user.date_joined

    headers = {'Authorization': f'bearer {token}',
               'Content-Type': 'application/json'}
    
    # Consulta à API GraphQL para obter os commits do usuário
    query = f"""
    {{
    viewer {{
        contributionsCollection(from:"{date}") {{
        totalCommitContributions
        }}
    }} 
    }} """

    # Envia uma requisição POST para a API GraphQL do GitHub
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query},
        headers=headers
    )

    if response.status_code != 200:
        return JsonResponse({'error': 'Error GraphQL', 'status_code': response.status_code}, status=500)

    data = response.json()

    total = data.get('data', {}) \
                    .get('viewer', {}) \
                   .get('contributionsCollection', {}) \
                   .get('totalCommitContributions', 0)

    return JsonResponse({
        'usuario': username,
        'total_commits': total, 
    })
