from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from levelhub.models import UserProfile

class UserSignupForm(UserCreationForm):
    #first_name = forms.CharField(max_length=30, help_text='Please enter your first name', required=False)
    #last_name = forms.CharField(max_length=30, help_text='Please enter your last name', required=False)
    #email = forms.EmailField(help_text='Please enter your email', required=False)

    class Meta:
        model = User
        #fields = ('username', 'first_name', 'last_name', 'email')
        fields = ('username', )


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('website',)