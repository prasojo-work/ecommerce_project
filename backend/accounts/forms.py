from django.contrib.auth.forms import (
    UserChangeForm as BaseUserChangeForm,
)
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
)

from accounts.models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name")


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = ("email", "full_name")
