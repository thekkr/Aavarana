from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile


class RegisterForm(UserCreationForm):
    username     = forms.CharField(
                       max_length=150,
                       required=True,
                       help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
                   )
    email        = forms.EmailField(required=True)
    first_name   = forms.CharField(max_length=150, required=True)
    last_name    = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model  = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email        = self.cleaned_data['email']
        user.first_name   = self.cleaned_data['first_name']
        user.last_name    = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    username     = forms.CharField(
                       max_length=150,
                       required=True,
                       help_text='Unique. Used to log in.',
                   )
    first_name   = forms.CharField(max_length=150, required=False)
    last_name    = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model  = Profile
        fields = ('avatar', 'default_avatar', 'bio', 'website')
        widgets = {
            'default_avatar': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial     = self.user.username
            self.fields['first_name'].initial   = self.user.first_name
            self.fields['last_name'].initial    = self.user.last_name
            self.fields['phone_number'].initial = self.user.phone_number

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = CustomUser.objects.filter(username__iexact=username)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username     = self.cleaned_data.get('username', self.user.username)
            self.user.first_name   = self.cleaned_data.get('first_name', '')
            self.user.last_name    = self.cleaned_data.get('last_name', '')
            self.user.phone_number = self.cleaned_data.get('phone_number', '')
            self.user.save()
        if commit:
            profile.save()
        return profile


class RoleChangeForm(forms.Form):
    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('author', 'Author'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your registered email'}),
    )
