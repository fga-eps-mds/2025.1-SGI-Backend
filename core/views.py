from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from core.models import Profile

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

def total_issues(request):
    #Retrieves the GitHub username and authentication token stored
    username = request.session.get('username')
    token = request.session.get('token')

    if not username or not token:
        return JsonResponse({'error': 'invalid'}, status=400)

    #Tries to find the user in the django database
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    profile, created = Profile.objects.get_or_create(user=user)

    #Gets the date the user was registered in the system used to filter issues until this moment onwards.
    date = user.date_joined

    #Creates a GraphQL query for GitHub and search the total number of issues created by the user since the date they logged in
    query = f"""
    {{
    search(query: "author:{username} type:issue created:>={date}", type: ISSUE, first: 1) {{
        issueCount
    }}
    }}
    """

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    #Sends the request to the GitHub API and stores the total number of issues created by the user
    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)

    data = response.json()
    total_issues = data['data']['search']['issueCount']

    #This time to count only the issues closed (state:closed) by the user since their entry.   
    query2 = f"""
    {{
    search(query: "author:{username} type:issue state:closed created:>={date}", type: ISSUE, first: 1) {{
        issueCount
    }}
    }}
    """

    response2 = requests.post("https://api.github.com/graphql", json={"query": query2}, headers=headers)

    data2 = response2.json()
    total_issues_closed = data2['data']['search']['issueCount']
    
    #Calculates the score based on closed issues
    profile.score_issues = total_issues_closed * 10
    profile.save()

   
    return JsonResponse({
        'username': username,
        'total_issues': total_issues,
        'total_issues_closed': total_issues_closed,
        'pontuação_issues': profile.score_issues,
    })

