from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    CustomUserChangeForm,
    CustomPasswordChangeForm
)
from django.contrib.auth import update_session_auth_hash

# 회원가입
# 안에 쓴 요청만 함수 안으로 들어가짐 / 예를 들어 put, delete 같은 다른 메서드로 요청하면 함수 실행 안하고 405 method not allowed 응답 
@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return redirect('books:index')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.interested_genres = ','.join(form.cleaned_data['interested_genres'])
            user.save()
            auth_login(request, user)
            return redirect('books:index')

    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/signup.html', context)

# 로그인
@require_http_methods(['GET', 'POST'])
def login(request):
    if request.user.is_authenticated:
        return redirect('books:index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('books:index')

    else: 
        form = CustomAuthenticationForm()

    context = {'form': form}
    return render(request, 'accounts/login.html', context)

# 로그아웃
@require_POST
def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('books:index')

# 회원 탈퇴
@require_POST
def delete(request):
    if request.user.is_authenticated:
        request.user.delete()
        auth_logout(request)
    return redirect('books:index')

@login_required
@require_http_methods(['GET', 'POST'])
def update(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance = request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.interested_genres = ','.join(form.cleaned_data['interested_genres'])
            user.save()
            return redirect('accounts:profile', request.user.username)
    else:
        genres = request.user.interested_genres
        initial = {'interested_genres': genres.split(',') if genres else []}
        form = CustomUserChangeForm(instance = request.user, initial=initial)

    context = {'form': form}
    return render(request, 'accounts/update.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('books:index')

    else:
        form = CustomPasswordChangeForm(request.user)

    context = {'form': form}
    return render(request, 'accounts/change_password.html', context)

# 프로필 페이지(마이페이지)
@login_required
@require_safe
def profile(request, username):
    person = get_object_or_404(get_user_model(), username=username)
    genres = person.interested_genres.split(',') if person.interested_genres else []
    context = {'person': person, 'genres': genres}
    return render(request, 'accounts/profile.html', context)