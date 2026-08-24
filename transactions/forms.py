from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Transaction

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']    

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ['user']


