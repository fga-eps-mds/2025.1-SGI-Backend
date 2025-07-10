from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from .models import Profile  

class TotalIssuesViewTest(TestCase):
    def setUp(self):
        #Create a test user
        self.user = User.objects.create_user(username='user_test', password='test123')
        self.user.save()

        #Creates an associated profile if the view's get_or_create needs it
        Profile.objects.create(user=self.user)

        #Define an example token
        self.token = 'fake-token'

        #Instantiate a Django client to simulate requests
        self.client = Client()

        #Save username and token in session
        session = self.client.session
        session['username'] = self.user.username
        session['token'] = self.token
        session.save()

    @patch('requests.post')
    def test_total_issues_success(self, mock_post):
        #Mock GitHub API response for first open issue query
        mock_post.side_effect = [
            MockResponse({'data': {'search': {'issueCount': 5}}}, 200),  #Total issues
            MockResponse({'data': {'search': {'issueCount': 3}}}, 200),  #Closed issues 
        ]

        response = self.client.get(reverse('total_issues'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        self.assertEqual(response.json()['total_issues'], 5)
        self.assertEqual(response.json()['total_issues_closed'], 3)
        self.assertEqual(response.json()['pontuação_issues'], 30)


#Helper class to simulate GitHub response
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code
    def json(self):
        return self._json
    
class ProfileModelTest(TestCase):
    def test_create_profile_with_default_score(self):
        #Create a test user
        user = User.objects.create_user(username='user_test', password='12345')

        #Create a related Profile
        profile = Profile.objects.create(user=user)

        #Tests if the Profile was created correctly
        self.assertEqual(profile.user.username, 'user_test')

        #Checks if the score starts with 0
        self.assertEqual(profile.pontuacao_issues, 0)

    def test_update_pontuacao_issues(self):
        user = User.objects.create_user(username='user_test2', password='abc123')
        profile = Profile.objects.create(user=user)

        #Update the score
        profile.pontuacao_issues = 50
        profile.save()

        #Recover again and test
        updated = Profile.objects.get(user=user)
        self.assertEqual(updated.pontuacao_issues, 50)