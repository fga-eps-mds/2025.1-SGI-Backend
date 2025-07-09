from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Score based on Commit activities
    pontuacao_commits = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Profile de {self.user.username} - Pontuação: {self.pontuacao_commits}"