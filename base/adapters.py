# in your_app/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If the user already exists, link accounts
        email = user_email(sociallogin.user)
        if not email:
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            existing_user = User.objects.get(email=email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
