from django import forms
from .models import USER_TYPE_CHOICES

# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    type = forms.ChoiceField(label='User type', choices=USER_TYPE_CHOICES)
    first_name = forms.CharField(label='Name', required=False)
    middle_name = forms.CharField(label='Middle name', required=False)
    last_name = forms.CharField(label='Last name', required=False)
    email = forms.EmailField(required=True)
    company = forms.CharField(label='Company', required=False)
    position = forms.CharField(label='Position', required=False)


    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']