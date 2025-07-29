from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class UsernameOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        user = None

        try:
            # ✅ اول با phone_number
            user = User.objects.get(phone_number=username)
        except User.DoesNotExist:
            try:
                # ❌ اگر نبود، با username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
