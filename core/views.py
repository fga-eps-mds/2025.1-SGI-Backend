from django.shortcuts import render, redirect
from django.conf import settings
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone

#Redirects the user to GitHub to authorize access
def git_auth_code(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    # Redirects to GitHub's login/authorization page
    return redirect(github_auth_url)

# Receives the "code" from GitHub and exchanges it for an access tokenn
def git_auth_token(request):
    code = request.GET.get('code')  # Gets the code returned by GitHub
    if not code:
        return JsonResponse({'error': 'No code provided by GitHub'}, status=400)

    # Sends a request to GitHub to exchange the code for an access token
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
    access_token = token_data.get('access_token')  # Gets the access token from the response
    request.session['token'] = access_token
    if not access_token:
        return JsonResponse({'error': 'Failed to obtain access token from GitHub'}, status=400)


    #Calls the function that creates the user based on the access token
    return create_user(request, access_token)

# Uses the GitHub token to get user data and create/login into Django
def create_user(request, access_token):
    #Gets basic user data (like login, name, etc.)
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'token {access_token}'}
    )
    user_data = user_response.json()

    # Gets the user's list of emails
    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={'Authorization': f'token {access_token}'}
    )
    emails = email_response.json()

    # Tries to find the primary and verified email
    username = user_data.get('login')
    request.session['username'] = username
    email = None
    for e in emails:
        if e.get('primary') and e.get('verified'):
            email = e.get('email')
            break

    if not email:
        return JsonResponse({'error': 'No verified primary email found in GitHub account'}, status=400)

    # Creates the local user (if not already existing) or fetches the existing one
    date = timezone.now()
    user, created = User.objects.get_or_create(username=username, defaults={'email': email,'date_joined': date})

    # Generates JWT tokens for the user (login without password!)
    refresh = RefreshToken.for_user(user)
    access_jwt = str(refresh.access_token)
    refresh_jwt = str(refresh)

    # Returns user data and tokens (if desired, tokens can be included too)
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
    
    # GraphQL api query to get the commits  of the user


    query = f"""
    {{
    viewer {{
        contributionsCollection(from:"{date}") {{
        totalCommitContributions
        }}
    }} 
    }} """
    # send a post request to the GitHub GraphQL api

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
        'total_commits': total

    })
