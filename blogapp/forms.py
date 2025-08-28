from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import URLValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from .models import UserProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already in use.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if not username.isalnum():
            raise ValidationError('Username must contain only letters and numbers.')
        return username

class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        validators=[MinLengthValidator(3, 'Username must be at least 3 characters long.')]
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        validators=[MinLengthValidator(8, 'Password must be at least 8 characters long.')]
    )

class BlogForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'My Blog'}),
        validators=[MinLengthValidator(2, 'Blog name must be at least 2 characters long.')]
    )
    url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        validators=[URLValidator(schemes=['http', 'https'])]
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        validators=[MinLengthValidator(2, 'Username must be at least 2 characters long.')]
    )
    apikey = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'API Key'}),
        validators=[MinLengthValidator(10, 'API key must be at least 10 characters long.')]
    )
    category = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category1, Category2'}),
        help_text='Enter categories separated by commas'
    )
    
    # def clean_name(self):
    #     name = self.cleaned_data.get('name')
    #     if not name.replace(' ', '').isalnum():
    #         raise ValidationError('Blog name can only contain letters, numbers, and spaces.')
    #     return name.strip()
    
    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category:
            categories = [cat.strip() for cat in category.split(',') if cat.strip()]
            if len(categories) > 10:
                raise ValidationError('Maximum 10 categories allowed.')
            for cat in categories:
                if len(cat) > 50:
                    raise ValidationError('Each category must be 50 characters or less.')
        return category

class ArticleForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Article Title'}),
        validators=[MinLengthValidator(5, 'Title must be at least 5 characters long.')]
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your article content here...'}),
        validators=[MinLengthValidator(50, 'Content must be at least 50 characters long.')]
    )
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    blog = forms.ModelChoiceField(
        queryset=None, 
        empty_label="Select a blog",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            from .models import Blog
            self.fields['blog'].queryset = Blog.objects.filter(user=user)
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.split()) < 10:
            raise ValidationError('Content must contain at least 10 words.')
        return content.strip()


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'age', 'gender', 'email', 'dob', 'picture'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if hasattr(profile, 'user') and profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', profile.user.first_name)
            profile.user.last_name = self.cleaned_data.get('last_name', profile.user.last_name)
            profile.user.email = self.cleaned_data.get('email', profile.user.email)
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile
