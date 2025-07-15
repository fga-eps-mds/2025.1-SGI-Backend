"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include 
from . import views
from .views import public_github_profile, user_profile, check_auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/github/', views.git_auth_code, name='git_auth_code'),
    #path('api/auth/token', views.git_auth_token, name='git_code_token'),
    path('callback/', views.git_auth_token, name='callback'),
    path('api/auth/logout/', views.logout, name='logout'),
    path('api/auth/check/', check_auth, name='check_auth'),
    path('api/users/me/', user_profile, name='user_profile'),
    path('DELETE/api/users/me/', views.delete_user,name='delete_user'),
    path('api/users/<str:username>/', public_github_profile),
    path('api/users/[id]/total_issues',views.total_issues,name = 'total_issues'),
    path('api/users/id/total_commits',views.total_commits,name='total_commits'),
    path('api/users/<int:id>/pull_request',views.total_prs,name='Total PullRequests'),
    path('api/users/[id]/pull_request_fechados',views.total_prs_closed,name='Total PullRequests Fechados'),
    # path('api/pontuar-commits/', views.pontuar_commits, name='pontuar_commits'),

]
