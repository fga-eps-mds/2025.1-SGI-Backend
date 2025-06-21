from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from django.views.decorators.csrf import csrf_exempt

GITHUB_CLIENT_ID = 'Ov23ligET1j33hxbkQ3A'
GITHUB_CLIENT_SECRET = '0c826bbb7c84292ec3dd466ffe92de9dbfa1bd2e'
GITHUB_REDIRECT_URI = "http://localhost:8000/callback"



def git_auth_code(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return redirect(github_auth_url)

def git_auth_token(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'No code provided by GitHub'}, status=400)

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
    access_token = token_data.get('access_token')
    if not access_token:
        return JsonResponse({'error': 'Failed to obtain access token from GitHub'}, status=400)

    # Aqui você pode retornar o token ou chamar a lógica de criar usuário
    #return JsonResponse({'access_token': access_token})
    return create_user(request,access_token)


def create_user(request, access_token):
    # Pega dados do usuário do GitHub
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()

    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()

    # Extrair username e email (usar o email principal e verificado)
    username = user_data.get('login')
    email = None
    for e in emails:
        if e.get('primary') and e.get('verified'):
            email = e.get('email')
            break

    if not email:
        return JsonResponse({'error': 'No verified primary email found in GitHub account'}, status=400)

    # Criar ou pegar usuário Django local
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})

    # Gerar token JWT para esse usuário
    refresh = RefreshToken.for_user(user)
    access_jwt = str(refresh.access_token)
    refresh_jwt = str(refresh)

    # Retornar os tokens como JSON
    return JsonResponse({
        'username': username,
        'email': email,
        'access_token': access_jwt,
        'refresh_token': refresh_jwt,
    })

def blacklist(request,acess_token):
    try:
        if not acess_token:
            return False
        token = RefreshToken(acess_token)
        token.blacklist()
        return True
    except TokenError:
        return False
    
@csrf_exempt # Decorador para permitir requisições POST sem CSRF, coloquei para testar no Insomnia
def logout(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    # Pegar o token do header Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'success': False, 'message': 'Token not provided'}, status=400)
    
    token = auth_header.split(' ')[1]
    
    try:
        # Usando o RefreshToken para invalidar o token
        refresh_token = RefreshToken(token)
        refresh_token.blacklist()
        return JsonResponse({'success': True, 'message': 'Logout successful'})
    except TokenError as e:
        return JsonResponse({'success': False, 'message': f'Invalid token: {str(e)}'}, status=400)
