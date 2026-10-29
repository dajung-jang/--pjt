from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

# 회원 가입 폼
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'last_name', 'first_name', 'email']
        widgets = {
            'username': forms.TextInput(
                attrs = {'placeholder': '아이디'}
            ),
            'last_name': forms.TextInput(
                attrs = {'placeholder': '성'}
            ),
            'first_name': forms.TextInput(
                attrs = {'placeholder': '이름'}
            ),
            'email': forms.EmailInput(
                attrs= {'placeholder': '이메일'}
            ),
        }
        labels = {
                'username': '아이디',
                'last_name': '성',
                'first_name': '이름',
                'email': '이메일',
            }

    field_order = ['username', 'password1', 'password2', 'last_name', 'first_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].widget.attrs['placeholder'] = '비밀번호'
        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].widget.attrs['placeholder'] = '비밀번호 확인'

# 로그인 폼
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['username'].label = '아이디'
        self.fields['username'].widget.attrs['placeholder'] = '아이디'
        self.fields['password'].label = '비밀번호'
        self.fields['password'].widget.attrs['placeholder'] = '비밀번호'
    
# 회원 정보 수정
class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = ['last_name', 'first_name', 'email']
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': '성'}),
            'first_name': forms.TextInput(attrs={'placeholder': '이름'}),
            'email': forms.EmailInput(attrs={'placeholder': '이메일'}),
        }
        labels = {
            'last_name': '성',
            'first_name': '이름',
            'email': '이메일',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

# 비밀번호 변경
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['old_password'].label = '기존 비밀번호'
        self.fields['new_password1'].label = '새 비밀번호'
        self.fields['new_password2'].label = '새 비밀번호 확인'
