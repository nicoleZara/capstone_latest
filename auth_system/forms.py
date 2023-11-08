from django import forms
from .models import UserProfile

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']


#


from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User  # Import the User model
from .models import UserProfile

class EditProfileForm(UserChangeForm):
    first_name = forms.CharField(max_length=30, required=False)  # Custom field for first name
    last_name = forms.CharField(max_length=30, required=False)  # Custom field for last name

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'gender', 'birthday', 'age', 'purpose']