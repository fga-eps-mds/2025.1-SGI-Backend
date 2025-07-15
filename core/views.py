from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

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
# seu_app/views.py

import requests
import os
from django.http import JsonResponse
# Remova 'from django.conf import settings' se não estiver usando em outro lugar
# e use os.environ.get() diretamente para consistência.

def git_auth_token(request):
    """
    Recebe o 'code' do GitHub, troca por um 'access_token', e lida com erros de forma detalhada.
    """
    print("--- [Callback] Iniciando processo de troca de token.") # Log de início

    # 1. Obter o 'code' da requisição
    code = request.GET.get('code')
    if not code:
        print("--- [Callback] ERRO: 'code' não encontrado na requisição.")
        return JsonResponse({'error': 'No code provided by GitHub'}, status=400)

    print(f"--- [Callback] Código recebido: {code[:10]}...")

    # 2. Preparar e enviar a requisição para o GitHub
    payload = {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': os.environ.get('GITHUB_REDIRECT_URI'),
    }
    headers = {'Accept': 'application/json'}

    print(f"--- [Callback] Enviando requisição para GitHub com Client ID: {payload['client_id']}")

    try:
        # Faz a requisição POST
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers=headers,
            data=payload
        )
        
        # Lança um erro se a resposta do GitHub for um erro HTTP (ex: 404, 500)
        response.raise_for_status()
        
        response_data = response.json()
        print(f"--- [Callback] Resposta JSON recebida do GitHub: {response_data}")

        # 3. Analisar a resposta do GitHub
        
        # PRIMEIRO, verificar se o GitHub retornou um erro específico
        if 'error' in response_data:
            error_details = response_data.get('error_description', 'No description from GitHub.')
            print(f"--- [Callback] ERRO do GitHub: {response_data['error']} - {error_details}")
            return JsonResponse({
                'error': 'GitHub returned an error.',
                'error_details': response_data 
            }, status=400)

        # SEGUNDO, verificar se o access_token existe
        access_token = response_data.get('access_token')
        if not access_token:
            print("--- [Callback] ERRO: Resposta do GitHub OK, mas sem access_token.")
            return JsonResponse({'error': 'Access token not found in GitHub response'}, status=400)

        # SUCESSO!
        print("--- [Callback] SUCESSO: Access token obtido.")
        request.session['jwt_token'] = access_token
        
        # Chama a próxima função para criar/logar o usuário
        return create_user(request, access_token)

    except requests.exceptions.RequestException as e:
        # Captura erros de rede ou status HTTP de erro (4xx, 5xx)
        print(f"--- [Callback] ERRO CRÍTICO de requisição: {e}")
        error_body = e.response.text if e.response else "No response body"
        print(f"--- [Callback] Corpo do erro do GitHub: {error_body}")
        return JsonResponse({'error': 'Failed to communicate with GitHub', 'details': error_body}, status=500)

    except ValueError:
        # Captura erro se a resposta não for um JSON válido
        print("--- [Callback] ERRO: Falha ao decodificar JSON da resposta do GitHub.")
        return JsonResponse({'error': 'Invalid response from GitHub'}, status=500)
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
        # Retornar os tokens como JSON ou redirecionar para o frontend
    frontend_url = f"{settings.CORS_ALLOWED_ORIGINS}/auth-success?access_token={access_jwt}&refresh_token={refresh_jwt}&username={username}&email={email}"
    return redirect(frontend_url)

def public_github_profile(request, username):
    
    #Access public data from github
    github_api_url = f"https://api.github.com/users/{username}"
    response = requests.get(github_api_url)

    #If the user not exist
    if response.status_code == 404:
        return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    #If they cant acess github
    if response.status_code != 200:
        return JsonResponse({'error': 'Error accessing GitHub'}, status=status.HTTP_502_BAD_GATEWAY)

    data = response.json()

    profile_data = {
        'name': data.get('name'),
        'avatar_url': data.get('avatar_url'),
        'bio': data.get('bio'),
    }

    return JsonResponse(profile_data)
@csrf_exempt # Decorador para permitir requisições POST sem CSRF, coloquei para testar no Insomnia
def delete_user(request):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Pegar o token JWT do header Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization token required'}, status=401)
    
    jwt_token = auth_header.split(' ')[1]
    
    try:
        # Decodificar o JWT para pegar informações do usuário
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(jwt_token)
        user_id = token['user_id']
        
        # Buscar o usuário pelo ID
        user = User.objects.get(id=user_id)
        username = user.username
        
        # Deletar o usuário
        user.delete()
        return JsonResponse({'message': f'User {username} deleted successfully.'})
        
    except TokenError:
        return JsonResponse({'error': 'Invalid or expired token'}, status=401)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to delete user: {str(e)}'}, status=500)

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

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Endpoint para obter informações do perfil do usuário autenticado"""
    user = request.user
    
    # Buscar dados atuais do GitHub para o usuário
    try:
        github_api_url = f"https://api.github.com/users/{user.username}"
        response = requests.get(github_api_url)
        
        if response.status_code == 200:
            github_data = response.json()
            profile_data = {
                'username': user.username,
                'email': user.email,
                'name': github_data.get('name') or user.username,
                'avatar_url': github_data.get('avatar_url'),
                'bio': github_data.get('bio'),
                'public_repos': github_data.get('public_repos', 0),
                'followers': github_data.get('followers', 0),
                'following': github_data.get('following', 0),
            }
        else:
            # Fallback para dados básicos se não conseguir acessar GitHub
            profile_data = {
                'username': user.username,
                'email': user.email,
                'name': user.username,
                'avatar_url': None,
                'bio': None,
                'public_repos': 0,
                'followers': 0,
                'following': 0,
            }
        
        return JsonResponse(profile_data)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching profile: {str(e)}'}, status=500)

@api_view(['GET'])
def check_auth(request):
    """Endpoint para verificar se o usuário está autenticado"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'authenticated': False}, status=200)
    
    jwt_token = auth_header.split(' ')[1]
    
    try:
        token = AccessToken(jwt_token)
        user_id = token['user_id']
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'authenticated': True,
            'username': user.username,
            'email': user.email
        })
    except (TokenError, User.DoesNotExist):
        return JsonResponse({'authenticated': False}, status=200)

def health_check(request):
    return JsonResponse({"status": "ok", "message": "SGI Backend is running!"})
