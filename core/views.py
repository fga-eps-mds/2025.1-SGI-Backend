from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from django.views.decorators.csrf import csrf_exempt

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
    request.session['jwt_token'] = access_token

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
    

    # Retornar os tokens como JSON
    return JsonResponse({
        'username': username,
        'email': email,
        'access_token': access_jwt,
        'refresh_token': refresh_jwt,
    })

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
