from django.contrib import admin
from .models import Blog, Article

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'url', 'username', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('name', 'url', 'username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'blog', 'status', 'created_at', 'updated_at', 'published_at')
    list_filter = ('status', 'created_at', 'updated_at', 'published_at', 'user', 'blog')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    filter_horizontal = ()
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'blog')
