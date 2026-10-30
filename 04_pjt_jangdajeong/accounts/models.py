from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]

    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(null = True, blank=True)
    weekly_reading_hours = models.PositiveIntegerField(null=True, blank=True)
    yearly_reading_count = models.PositiveIntegerField(null=True, blank=True)
    interested_genres = models.CharField(max_length=600, blank=True)
    