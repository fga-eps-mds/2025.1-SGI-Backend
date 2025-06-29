from django.db import models
from django.contrib.auth.models import User

class CommitScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    commit_sha = models.CharField(max_length=40, unique=True) # Usuário associado ao commit 
    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scored_at']  # Úteis para consultas

    def __str__(self):
        return f"Commit {self.commit_sha[:7]} by {self.user.username}"

    def add_authors(self, main_user, co_authors_emails):
        """Registra autores do commit"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Adiciona autor principal
        CommitAuthor.objects.create(
            commit=self,
            user=main_user,
            is_main_author=True
        )
        
        # Adiciona co-autores
        for email in co_authors_emails:
            try:
                user = User.objects.get(email=email)
                CommitAuthor.objects.create(
                    commit=self,
                    user=user,
                    is_main_author=False
                )
            except User.DoesNotExist:
                continue
    

class UserScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)

    def add_points(self, points):
        """Método seguro para adicionar pontos"""
        self.total_points += points
        self.save()

    def __str__(self):
        return f"{self.user.username}: {self.total_points} pontos"
    
    @classmethod
    def award_points_for_commit(cls, commit_sha, main_user, co_authors_emails, points=10):
        """Método estático para pontuar todos os autores de um commit"""
        with transaction.atomic():
            commit, created = CommitScore.objects.get_or_create(
                commit_sha=commit_sha,
                defaults={'user': main_user}
            )
            
            if created:
                commit.add_authors(main_user, co_authors_emails)
                
                # Pontua todos os autores
                authors = CommitAuthor.objects.filter(commit=commit)
                for author in authors:
                    user_score, _ = cls.objects.get_or_create(user=author.user)
                    user_score.add_points(points)
                
                return True
            return False

class CommitAuthor(models.Model):
    commit = models.ForeignKey(CommitScore, on_delete=models.CASCADE, related_name='authors')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_main_author = models.BooleanField(default=False) # Flag de autor principal

    class Meta:
        unique_together = ('commit', 'user')  # Evita duplicatas