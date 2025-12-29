from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # 1. If the Google account is already linked, let them in.
        if sociallogin.is_existing:
            return

        # 2. If not linked, check if a user with this email ALREADY exists in the DB
        email = sociallogin.user.email
        if email:
            try:
                existing_user = User.objects.get(email=email)
                
                # OPTIONAL: You can check existing_user.check_password() here 
                # or verify email if strict security is needed.
                
                # Link this new Google login to the existing user
                sociallogin.connect(request, existing_user)
                
                # Return allows the login process to continue naturally now that it's linked
                return 
            
            except User.DoesNotExist:
                # 3. If no user exists, AND it's not linked, send to register
                pass

        # If we reach here, it's a truly new user. Redirect to your custom register page.
        raise ImmediateHttpResponse(redirect('/register/'))