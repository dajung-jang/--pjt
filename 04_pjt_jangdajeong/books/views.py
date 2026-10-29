from django.shortcuts import render

def index(request):
    return render(request, 'books/index.html')

def create(request):
    return render(request, 'books/create.html')