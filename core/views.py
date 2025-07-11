from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
import calendar
import datetime
from collections import defaultdict
from django.utils.timezone import localtime
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

def total_points_stats(request):
    username = request.session.get('username')
    token = request.session.get('token')
    user = User.objects.get(username=username)

    start = user.date_joined.date().replace(day=1)  
    today = timezone.now().date().replace(day=1)    

    results_requests = {}

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    while start<=today:
        next_month = (start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        end = next_month - datetime.timedelta(days=1)
        month = start.strftime('%m')
        year = start.strftime('%Y')
        key = f"{year}-{month}"

        query_commits = f"""
        {{
          viewer {{
            contributionsCollection(from: "{start}", to: "{end}") {{
              totalCommitContributions
            }}
          }}
        }}
        """
        response_commits = requests.post("https://api.github.com/graphql", json={"query": query_commits}, headers=headers)
        data = response_commits.json()

        commits = data.get('data', {}) \
                    .get('viewer', {}) \
                   .get('contributionsCollection', {}) \
                   .get('totalCommitContributions', 0)
        total_points_commits = commits*10

        query_issues = f"""
        {{
          search(query: "author:{username} type:issue created:{start}..{end}", type: ISSUE, first: 1) {{
            issueCount
          }}
        }}
        """
        response_issues = requests.post("https://api.github.com/graphql", json={"query": query_issues}, headers=headers)
        data = response_issues.json()
        issues = data['data']['search']['issueCount']
        total_points_issues = issues * 10

        query_open_prs = f"""
        query {{
        search(query: "is:pr is:open author:{username} created:{start}..{end}", type: ISSUE, first: 1) {{
            issueCount
        }}
        }}
        """
        response_open_prs = requests.post("https://api.github.com/graphql", json={"query": query_open_prs}, headers=headers)
        data = response_open_prs.json()
        open_prs = data['data']['search']['issueCount']
        total_points_open_prs = open_prs *10

        query_appr_prs = f"""
        {{
          search(query: "is:pr is:open review:approved author:{username} created:{start}..{end}", type: ISSUE, first: 1) {{
            issueCount
          }}
        }}
        """
        response_appr_prs = requests.post("https://api.github.com/graphql", json={"query": query_appr_prs}, headers=headers)
        data = response_appr_prs.json()
        appr_prs = data['data']['search']['issueCount']
        total_points_appr_prs = appr_prs * 10


        query_merges= f"""
        {{
          search(query: "is:pr is:merged merged-by:{username} created:{start}..{end}", type: ISSUE, first: 1) {{
            issueCount
          }}
        }}
        """
        response_merges = requests.post("https://api.github.com/graphql", json={"query": query_merges}, headers=headers)
        data = response_merges.json()
        merges = data['data']['search']['issueCount']
        total_merge_points = merges * 10


        total_month = total_points_commits + total_points_issues + total_points_open_prs + total_points_appr_prs + total_merge_points
        results_requests[key] = total_month

        start = next_month
    return JsonResponse({
    'username': username,
    'points_y/m': results_requests
    })

