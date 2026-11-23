from django.db import models
from django.utils import timezone


class Book(models.Model):
    book_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    author_name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='books/')
    pdf = models.FileField(
        upload_to='books/pdfs/',
        blank=True,
        null=True
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8, blank=True)
    pages = models.PositiveIntegerField(default=280, blank=True, null=True)
    language = models.CharField(max_length=50, default='English', blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.book_name
