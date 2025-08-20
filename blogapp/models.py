from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Blog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    username = models.CharField(max_length=50)
    apikey = models.CharField(max_length=255)
    category = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def get_categories_display(self):
        return ', '.join(self.category) if self.category else 'No categories'

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        words_per_minute = 200
        word_count = len(self.content.split())
        return max(1, round(word_count / words_per_minute))
