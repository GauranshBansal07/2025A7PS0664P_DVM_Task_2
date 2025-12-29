from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.user.email
        if email:
            try:
                existing_user = User.objects.get(email=email)

                sociallogin.connect(request, existing_user)
                
                return 
            
            except User.DoesNotExist:
                pass

        raise ImmediateHttpResponse(redirect('/register/'))