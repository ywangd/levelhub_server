from django import forms
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    username = forms.EmailField(help_text="Please enter an username.")
    password = forms.CharField(widget=forms.PasswordInput(), help_text="Please enter a password.")

    class Meta:
        model = User
        fields = ('username', 'password')
