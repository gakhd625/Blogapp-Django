from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Blog, Article, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except:
            return 'No Role'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

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
