from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class LoginPageTests(TestCase):
    """Tests for the login page functionality"""

    def setUp(self):
        """Set up test client and create a test user"""
        self.client = Client()
        self.login_url = reverse('login')
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/login.html')

    def test_login_page_contains_form(self):
        """Test that login page contains the login form"""
        response = self.client.get(self.login_url)
        self.assertContains(response, 'Welcome back')
        self.assertContains(response, 'id="username"')
        self.assertContains(response, 'id="password"')
        self.assertContains(response, 'Sign In')

    def test_login_page_has_active_nav(self):
        """Test that login navigation link has active class"""
        response = self.client.get(self.login_url)
        self.assertContains(response, 'cta-login active')

    def test_successful_login(self):
        """Test successful login with valid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 302)

    def test_failed_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page or show error
        self.assertEqual(response.status_code, 200)

    def test_failed_login_empty_username(self):
        """Test login fails with empty username"""
        response = self.client.post(self.login_url, {
            'username': '',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)

    def test_failed_login_empty_password(self):
        """Test login fails with empty password"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)

    def test_login_page_csrf_token(self):
        """Test that login form has CSRF token"""
        response = self.client.get(self.login_url)
        self.assertContains(response, 'csrfmiddlewaretoken')


class SignupPageTests(TestCase):
    """Tests for the signup page functionality"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.signup_url = reverse('signup')

    def test_signup_page_loads(self):
        """Test that signup page loads successfully"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/signup.html')

    def test_signup_page_contains_form(self):
        """Test that signup page contains the signup form"""
        response = self.client.get(self.signup_url)
        self.assertContains(response, 'Create your account')
        self.assertContains(response, 'id="email"')
        self.assertContains(response, 'id="username"')
        self.assertContains(response, 'id="password1"')
        self.assertContains(response, 'id="password2"')
        self.assertContains(response, 'Create Account')

    def test_signup_page_has_active_nav(self):
        """Test that signup navigation link has active class"""
        response = self.client.get(self.signup_url)
        self.assertContains(response, 'cta-signup active')

    def test_successful_signup(self):
        """Test successful signup with valid data"""
        response = self.client.post(self.signup_url, {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123'
        })
        # Should redirect after successful signup
        self.assertEqual(response.status_code, 302)
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_failed_signup_password_mismatch(self):
        """Test signup fails when passwords don't match"""
        response = self.client.post(self.signup_url, {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'differentpass123'
        })
        self.assertEqual(response.status_code, 200)
        # User should not be created
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_failed_signup_duplicate_username(self):
        """Test signup fails with duplicate username"""
        # Create a user first
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
        # Try to create another user with same username
        response = self.client.post(self.signup_url, {
            'email': 'newuser@example.com',
            'username': 'existinguser',
            'password1': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertEqual(response.status_code, 200)

    def test_failed_signup_invalid_email(self):
        """Test signup fails with invalid email"""
        response = self.client.post(self.signup_url, {
            'email': 'invalidemail',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_failed_signup_empty_fields(self):
        """Test signup fails with empty required fields"""
        response = self.client.post(self.signup_url, {
            'email': '',
            'username': '',
            'password1': '',
            'password2': ''
        })
        self.assertEqual(response.status_code, 200)

    def test_signup_page_csrf_token(self):
        """Test that signup form has CSRF token"""
        response = self.client.get(self.signup_url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_signup_link_to_login(self):
        """Test that signup page has link to login"""
        response = self.client.get(self.signup_url)
        self.assertContains(response, 'Already have an account?')
        self.assertContains(response, reverse('login'))


class NavigationTests(TestCase):
    """Tests for navigation consistency across pages"""

    def setUp(self):
        self.client = Client()

    def test_login_page_navigation(self):
        """Test navigation structure on login page"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'Home')
        self.assertContains(response, 'About')
        self.assertContains(response, 'Services')
        self.assertContains(response, 'Contact')
        self.assertContains(response, 'Log In')
        self.assertContains(response, 'Sign Up')

    def test_signup_page_navigation(self):
        """Test navigation structure on signup page"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'Home')
        self.assertContains(response, 'About')
        self.assertContains(response, 'Services')
        self.assertContains(response, 'Contact')
        self.assertContains(response, 'Log In')
        self.assertContains(response, 'Sign Up')

    def test_login_page_has_logo(self):
        """Test that login page displays logo"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'FRI Logo')

    def test_signup_page_has_logo(self):
        """Test that signup page displays logo"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'FRI Logo')


class PasswordToggleTests(TestCase):
    """Tests for password visibility toggle functionality"""

    def setUp(self):
        self.client = Client()

    def test_login_page_has_password_toggle(self):
        """Test that login page has password toggle button"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'togglePassword')
        self.assertContains(response, 'fa-eye')

    def test_signup_page_has_password_toggles(self):
        """Test that signup page has password toggle buttons for both fields"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'togglePassword')
        self.assertContains(response, 'password1-toggle-icon')
        self.assertContains(response, 'password2-toggle-icon')


class FormValidationTests(TestCase):
    """Tests for client-side form validation attributes"""

    def setUp(self):
        self.client = Client()

    def test_login_form_required_fields(self):
        """Test that login form fields have required attribute"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'required')

    def test_signup_form_required_fields(self):
        """Test that signup form fields have required attribute"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'required')

    def test_signup_email_field_type(self):
        """Test that email field has correct type"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'type="email"')
