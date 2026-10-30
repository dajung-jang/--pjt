from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe, require_POST
from .models import Book
from .forms import BookForm

@require_safe
def index(request):
    books = Book.objects.all()
    context = {'books': books}
    return render(request, 'books/index.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            return redirect('books:detail', book.pk)
    else:
        form = BookForm()

    context = {'form': form}
    return render(request, 'books/create.html', context)


@require_safe
def detail(request, pk):
    book = get_object_or_404(Book, pk = pk)
    context = {'book': book}
    return render(request, 'books/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def update(request, pk):
    book = get_object_or_404(Book, pk = pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance = book)
        if form.is_valid():
            form.save()
            return redirect('books:detail', book.pk)
    else:
        form = BookForm(instance = book)

    context = {'form': form, 'book': book}
    return render(request, 'books/update.html', context)


@login_required
@require_POST
def delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect('books:index')
