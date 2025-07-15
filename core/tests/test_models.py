from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Profile

class ProfileModelTest(TestCase):
    # Prepare the environment for tests
    def setUp(self):
        self.user = User.objects.create_user(
            username='user_teste',
            email='user@example.com',
            password='senha123'
        )

    def test_profile_creation_with_default_score(self):
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.pontuacao_commits, 0)

    def test_str_representation(self):
        profile = Profile.objects.create(user=self.user, pontuacao_commits=15)
        self.assertEqual(str(profile), f"Profile de {self.user.username} - Pontuação: 15")


