from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse

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

def create_user_and_redirect(request, access_token):
    """
    Usa o access_token para pegar os dados do usuário, criar/logar no sistema,
    gerar tokens JWT e redirecionar para o frontend.
    """
    try:
        # Pega os dados do usuário
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get("https://api.github.com/user", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        # Pega os e-mails do usuário
        email_response = requests.get("https://api.github.com/user/emails", headers=headers)
        email_response.raise_for_status()
        emails = email_response.json()

        # Encontra o e-mail primário e verificado
        primary_email = None
        for email_obj in emails:
            if email_obj.get('primary') and email_obj.get('verified'):
                primary_email = email_obj.get('email')
                break
        
        if not primary_email:
            return JsonResponse({'error': 'No verified primary email found on GitHub.'}, status=400)

        username = user_data.get('login')

        # Cria ou atualiza o usuário no banco de dados do Django
        user, created = User.objects.update_or_create(
            username=username,
            defaults={'email': primary_email}
        )

        # Gera os tokens JWT para o frontend usar
        refresh = RefreshToken.for_user(user)
        access_jwt = str(refresh.access_token)
        refresh_jwt = str(refresh)

        # Constrói a URL de redirecionamento para o seu frontend
        frontend_url = config('FRONTEND_URL') # Lê a URL base do seu frontend
        redirect_url = (
            f"{frontend_url}/auth/success"
            f"?access_token={access_jwt}"
            f"&refresh_token={refresh_jwt}"
        )
        
        # Redireciona o navegador do usuário para o frontend com os tokens na URL
        return redirect(redirect_url)

    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching user data from GitHub: {e}")
        return JsonResponse({'error': 'Failed to fetch user data from GitHub.'}, status=502)
    except Exception as e:
        print(f"An unexpected error occurred in create_user: {e}")
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)
