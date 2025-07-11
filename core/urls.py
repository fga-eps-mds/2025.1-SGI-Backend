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

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('api/auth/github', views.git_auth_code, name='git_auth_code'),
    #path('api/auth/token', views.git_auth_token, name='git_code_token'),
    path('callback', views.git_auth_token, name='callback'),
    path('api/users/totalCommitsMes', views.totalCommitsMes, name='totalCommitsMes')

    
    


    #path('callback', views.callback, name='callback'),
    #path('auth/', include('social_django.urls', namespace='social')),  links de auth do django 
]
