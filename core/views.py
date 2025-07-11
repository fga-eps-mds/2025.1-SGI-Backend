from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
import calendar
from datetime import datetime
from collections import defaultdict
from django.utils.timezone import localtime


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

# Recebe o "code" do GitHub e troca por um access token
def git_auth_token(request):
    code = request.GET.get('code')  # Pega o code que o GitHub enviou de volta
    if not code:
        return JsonResponse({'error': 'No code provided by GitHub'}, status=400)

    # Envia uma requisição para o GitHub para trocar o code por um access token
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
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')  # Pega o access token da resposta
    if not access_token:
        return JsonResponse({'error': 'Failed to obtain access token from GitHub'}, status=400)

    # Chama a função que cria o usuário com base no access token
    return create_user(request, access_token)

# Usa o token do GitHub para pegar dados do usuário e criar/login no Django
def create_user(request, access_token):
    # Pega os dados básicos do usuário (como login, nome, etc.)
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()

    # Pega a lista de e-mails do usuário
    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()

    # Tenta achar o e-mail principal e verificado
    username = user_data.get('login')
    email = None
    for e in emails:
        if e.get('primary') and e.get('verified'):
            email = e.get('email')
            break

    if not email:
        return JsonResponse({'error': 'No verified primary email found in GitHub account'}, status=400)

    # Cria o usuário local (caso ainda não exista) ou pega o existente
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})

    # Gera tokens JWT para o usuário (login sem senha!)
    refresh = RefreshToken.for_user(user)
    access_jwt = str(refresh.access_token)
    refresh_jwt = str(refresh)

    # Retorna os dados do usuário e tokens (se quiser, pode incluir os tokens também)
    return JsonResponse({
        'username': username,
        'email': email,

    })

def totalCommitsMes(request):
    username = request.session.get('username')
    token = request.session.get('token')

    if not username or not token:
        return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)

    

    
    query = f"""
    query {{
      user(login: "{username}") {{
        contributionsCollection {{
          commitContributionsByRepository(maxRepositories: 100) {{
            repository {{
              name
            }}
            contributions(first: 100) {{
              nodes {{
                occurredAt
              }}
            }}
          }}
        }}
      }}
    }}
    """

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)

    if response.status_code != 200:
        return JsonResponse({'error': 'Erro na requisição ao GitHub'}, status=500)

    try:
        contribs = response.json()["data"]["user"]["contributionsCollection"]["commitContributionsByRepository"]
    except (KeyError, TypeError):
        return JsonResponse({'error': 'Erro ao processar resposta do GitHub'}, status=500)

    
    commitsMes = defaultdict(int)
    for repo_contrib in contribs:
        for node in repo_contrib["contributions"]["nodes"]:
            data_iso = node["occurredAt"]
            try:
                dt = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
                dt_local = localtime(dt)
                chave = (dt_local.year, dt_local.month)
                commitsMes[chave] += 1
            except ValueError:
                continue 

    resultado = [
        {
            "mes": calendar.month_name[mes].lower(),
            "ano": ano,
            "commits": qtd
        }
        for (ano, mes), qtd in sorted(commitsMes.items())
    ]

    return JsonResponse({"total_commits_por_mes": resultado})

