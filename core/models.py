from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Score based on Commit activities
    pontuacao_commits = models.IntegerField(default=0)

