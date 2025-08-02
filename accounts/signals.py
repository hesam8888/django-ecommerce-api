from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def set_login_method_on_social_signup(request, user, **kwargs):
    if hasattr(user, 'socialaccount_set') and user.socialaccount_set.filter(provider='google').exists():
        user.login_method = 'google'
        user.save() 