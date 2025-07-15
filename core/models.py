from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    pontuacao_issues = models.IntegerField(default=0)
    pontuacao_commits = models.IntegerField(default=0)
    pontuacao_prs = models.IntegerField(default=0)
    pontuacao_prs_fechados = models.IntegerField(default=0)
    pontos_prs_abertos = models.IntegerField(default=0)
    pontos_prs_approved = models.IntegerField(default=0)
    pontos_merge = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile de {self.user.username} - Total: {self.pontuacao_total}"
    
    @property
    def pontuacao_total(self):
        """Calcula a pontuação total do usuário"""
        return (
            self.pontuacao_issues + 
            self.pontuacao_commits + 
            self.pontuacao_prs + 
            self.pontuacao_prs_fechados
        )

# Creates/updates the profile automatically by saving the user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure profile exists for existing users
        profile, created = Profile.objects.get_or_create(user=instance)
