from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
import requests

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from decouple import config

@api_view(['GET'])
def git_auth_code(request):
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={config('GITHUB_CLIENT_ID')}"
        f"&redirect_uri={config('GITHUB_REDIRECT_URI')}"
        f"&scope=user:email"
    )
    return redirect(github_auth_url)

@api_view(['GET'])
def git_auth_token(request):
    code = request.GET.get('code')
    if not code:
        return Response({'error': 'Authorization code not provided by GitHub'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                'client_id': config('GITHUB_CLIENT_ID'),
                'client_secret': config('GITHUB_CLIENT_SECRET'),
                'code': code,
                'redirect_uri': config('GITHUB_REDIRECT_URI'),
            },
            headers={'Accept': 'application/json'}
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        github_access_token = token_data.get('access_token')

        if not github_access_token:
            return Response({'error': 'Failed to obtain access token from GitHub', 'details': token_data}, status=status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException as e:
        return Response({'error': 'Network error while contacting GitHub', 'details': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    auth_header = {'Authorization': f'Bearer {github_access_token}'}
    try:
        user_response = requests.get("https://api.github.com/user", headers=auth_header)
        user_response.raise_for_status()
        user_data = user_response.json()

        email_response = requests.get("https://api.github.com/user/emails", headers=auth_header)
        email_response.raise_for_status()
        emails = email_response.json()

    except requests.exceptions.RequestException as e:
        return Response({'error': 'Network error while fetching user data from GitHub', 'details': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    primary_email = None
    if isinstance(emails, list):
        for email_data in emails:
            if email_data.get('primary') and email_data.get('verified'):
                primary_email = email_data.get('email')
                break

    if not primary_email:
        return Response({'error': 'No verified primary email found in GitHub account.'}, status=status.HTTP_400_BAD_REQUEST)

    username = user_data.get('login')
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': primary_email, 'first_name': user_data.get('name', '')}
    )

    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'User authenticated successfully!',
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'username': user.username,
            'email': user.email,
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    profile_data = {
        'username': user.username,
        'email': user.email,
        'name': user.first_name or user.username,
    }
    try:
        github_response = requests.get(f"https://api.github.com/users/{user.username}")
        if github_response.status_code == 200:
            github_data = github_response.json()
            profile_data.update({
                'avatar_url': github_data.get('avatar_url'),
                'bio': github_data.get('bio'),
                'public_repos': github_data.get('public_repos', 0),
                'followers': github_data.get('followers', 0),
                'following': github_data.get('following', 0),
            })
    except requests.exceptions.RequestException:
        pass

    return Response(profile_data)

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request):
    user = request.user
    username = user.username
    user.delete()
    return Response({'message': f'User {username} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({
        'authenticated': True,
        'user': {
            'username': request.user.username,
            'email': request.user.email
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful.'}, status=status.HTTP_200_OK)
    except KeyError:
        return Response({'error': 'Refresh token not provided in request body.'}, status=status.HTTP_400_BAD_REQUEST)
    except TokenError:
        return Response({'error': 'Invalid or expired refresh token.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def public_github_profile(request, username):
    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        response.raise_for_status()
        data = response.json()
        profile_data = {
            'name': data.get('name'),
            'avatar_url': data.get('avatar_url'),
            'bio': data.get('bio'),
        }
        return Response(profile_data)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return Response({'error': 'GitHub user not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'Error accessing GitHub API', 'details': str(e)}, status=e.response.status_code)
    except requests.exceptions.RequestException as e:
        return Response({'error': 'Network error', 'details': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok", "message": "SGI Backend is running!"})
