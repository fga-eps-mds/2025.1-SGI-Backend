from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from core.models import Profile
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone 


# Redireciona o usuário para o GitHub para autorizar o acesso
@require_http_methods(["GET"])
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
@require_http_methods(["GET"])
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
    request.session['jwt_token'] = access_token

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
        # Retornar os tokens como JSON ou redirecionar para o frontend
    frontend_url = f"http://localhost:3000/auth-success?access_token={access_jwt}&refresh_token={refresh_jwt}&username={username}&email={email}"
    return redirect(frontend_url)

@require_http_methods(["GET"])
def total_commits(request):
    username = request.session.get('username')
    token = request.session.get('token')
    
    # Validação dos dados da sessão
    if not username or not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    date = user.date_joined
   
   # Creates the profile associated with the user to store the score
    profile, created = Profile.objects.get_or_create(user=user)

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

# calculates the score and saves in the profile
    profile.pontuacao_commits = total *10
    profile.save()

    return JsonResponse({
        'usuario': username,
        'total_commits': total, 
        'pontuacao_commits':profile.pontuacao_commits

    })

@require_http_methods(["GET"])
def total_prs(request):
    username = request.session.get('username')
    token = request.session.get('token')
    
    # Validação dos dados da sessão
    if not username or not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    date = user.date_joined

    # Creates the profile associated with the user to store the score
    profile, created = Profile.objects.get_or_create(user=user)

    query = f"""
    query {{
      search(query: "is:pr author:{username} created:>={date}", type: ISSUE, first: 1) {{
        issueCount
      }}
    }}
    """

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)

    if response.status_code != 200:
        return JsonResponse({'error': 'Error GraphQL', 'status_code': response.status_code}, status=500)

    data = response.json()
    totalpr = data["data"]["search"]["issueCount"]
    profile.pontos_prs_abertos = totalpr*10
    total_prs = data.get('data', {}).get('search', {}).get('issueCount', 0)

    # Calculates the score based on pull requests
    profile.pontuacao_prs = total_prs * 15
    profile.save()

    return JsonResponse({
        'username': username,
        'total_prs': total_prs,
        'pontuacao_prs': profile.pontuacao_prs
    })
        

@require_http_methods(["GET"])        
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


@require_http_methods(["GET"])
def total_issues(request):
    #Retrieves the GitHub username and authentication token stored
    username = request.session.get('username')
    token = request.session.get('token')

    if not username or not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)

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

    if response.status_code != 200:
        return JsonResponse({'error': 'Error GraphQL', 'status_code': response.status_code}, status=500)

    data = response.json()
    total_issues = data.get('data', {}).get('search', {}).get('issueCount', 0)

    #This time to count only the issues closed (state:closed) by the user since their entry.   
    query2 = f"""
    {{
    search(query: "author:{username} type:issue state:closed created:>={date}", type: ISSUE, first: 1) {{
        issueCount
    }}
    }}
    """

    response2 = requests.post("https://api.github.com/graphql", json={"query": query2}, headers=headers)

    if response2.status_code != 200:
        return JsonResponse({'error': 'Error GraphQL on second query', 'status_code': response2.status_code}, status=500)

    data2 = response2.json()
    total_issues_closed = data2.get('data', {}).get('search', {}).get('issueCount', 0)
    
    #Calculates the score based on closed issues
    profile.pontuacao_issues = total_issues_closed * 10
    profile.save()

    return JsonResponse({
        'username': username,
        'total_issues': total_issues,
        'total_issues_closed': total_issues_closed,
        'pontuacao_issues': profile.pontuacao_issues,
    })
