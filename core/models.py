from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    pontuacao_issues = models.IntegerField(default=0)
    pontuacao_commits = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile de {self.user.username} - Pontuação: {self.pontuacao_commits}"

# Creates/updates the profile automatically by saving the user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
