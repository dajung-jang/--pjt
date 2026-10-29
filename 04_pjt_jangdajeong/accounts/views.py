from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
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
            user = form.save()
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
            form.save()
            return redirect('books:index')
    else:
        form = CustomUserChangeForm(instance = request.user)

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