from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'description', 'customer_review_rank', 'author']
        wedgets = {
            'title': forms.TextInput(attrs={'palceholder': '제목'}),
            'description': forms.TextInput(attrs={'palceholder': '설명', 'rows': 5}),
            'customer_review_rank': forms.NumberInput(attrs={'palceholder': '1~10'}),
            'author': forms.TextInput(attrs={'palceholder': '저자'}),
        }
        labels = {
            'title': '제목',
            'description': '설명',
            'customer_review_rank': '회원 리뷰 평점',
            'author': '저자',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'