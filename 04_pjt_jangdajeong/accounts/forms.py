from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

GENDER_CHOICES = [
    ('소설/시/희곡', '소설/시/희곡'),
    ('경제/경영', '경제/경영'),
    ('자기계발', '자기계발'),
    ('인문/교양', '인문/교양'),
    ('과학', '과학'),
    ('취미/실용', '취미/실용'),
    ('어린이/청소년', '어린이/청소년'),
]

# 회원 가입 폼
class CustomUserCreationForm(UserCreationForm):
    interested_genres = forms.MultipleChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='관심 장르',
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = [
            'username', 'last_name', 'first_name', 'email',
            'gender', 'age', 'weekly_reading_hours', 'yearly_reading_count', 'interested_genres',
            ]
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
                'gender': '성별',
                'age': '나이',
                'weekly_reading_hours': '주간 평균 독서 시간(시간)',
                'yearly_reading_count': '연간 독서량(권)',
            }

    field_order = [
    'username', 'password1', 'password2', 'last_name', 'first_name', 'email',
    'gender', 'age', 'weekly_reading_hours', 'yearly_reading_count',
    'interested_genres',
]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'interested_genres':
                continue
            elif name == 'gender':
                field.widget.attrs['class'] = 'form-select'
            else:
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

    interested_genres = forms.MultipleChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='관심 장르',
    )

    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = [
            'last_name', 'first_name', 'email',
            'gender', 'age', 'weekly_reading_hours', 'yearly_reading_count',
            'interested_genres',
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': '성'}),
            'first_name': forms.TextInput(attrs={'placeholder': '이름'}),
            'email': forms.EmailInput(attrs={'placeholder': '이메일'}),
        }
        labels = {
            'last_name': '성',
            'first_name': '이름',
            'email': '이메일',
            'gender': '성별',
            'age': '나이',
            'weekly_reading_hours': '주간 평균 독서 시간(시간)',
            'yearly_reading_count': '연간 독서량(권)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'interested_genres':
                continue
            elif name == 'gender':
                field.widget.attrs['class'] = 'form-select'
            else:
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
