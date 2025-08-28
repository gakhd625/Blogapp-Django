from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from .models import Blog, Article
import json

# blogs = [
#     {"name": "Rakurin's Blog", "url": "https://rakurin.net/blog/", "username": "ra781228", "apikey": "********", "category": ["HELLOW WORLD"]},
# ]

# articles = [
#     {"title": "How to Write a Blog with AI", "date": "2024-06-01 10:00", "status": "Published"},
#     {"title": "SEO-Friendly Article Structure", "date": "2024-06-01 09:30", "status": "Draft"}
# ]
from .models import Blog, Article, UserProfile
from .services import GeminiService
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if not request.user.profile.is_admin:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('home')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validation
        if not all([username, email, password1, password2]):
            messages.error(request, 'All fields are required!')
            return render(request, 'registration/register.html')
        
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'registration/register.html')
        
        if not username.isalnum():
            messages.error(request, 'Username must contain only letters and numbers.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'registration/register.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'registration/register.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'registration/register.html')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'registration/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def home(request):
    if not request.user.is_authenticated:
        return render(request, "landing.html")
    articles = Article.objects.all()
    return render(request, "home.html", {"articles": articles})

def landing(request):
    return render(request, "landing.html")

@login_required
def blog_view(request, id):
    blog = Blog.objects.filter(id=id, user=request.user).first()
    articles = Article.objects.filter(blog_id=id, user=request.user)
    return render(request, "blogs/blog_view.html", {"blog": blog, "articles": articles})

@admin_required
def blog_registration(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        url = request.POST.get("url", "").strip()
        username = request.POST.get("username", "").strip()
        apikey = request.POST.get("apikey", "").strip()
        category_input = request.POST.get("category", "").strip()
        if not all([name, url, username, apikey]):
            messages.error(request, "All fields are required!")
            return render(request, "blogs/blog_registration.html", {"blogs": []})
        
        if len(name) < 2:
            messages.error(request, "Blog name must be at least 2 characters long.")
            return render(request, "blogs/blog_registration.html", {"blogs": []})

        if not url.startswith(('http://', 'https://', 'www.')):
            messages.error(request, "URL must start with http:// or https:// or www.")
            return render(request, "blogs/blog_registration.html", {"blogs": []})

        if len(username) < 2:
            messages.error(request, "Username must be at least 2 characters long.")
            return render(request, "blogs/blog_registration.html", {"blogs": []})

        if len(apikey) < 10:
            messages.error(request, "API key must be at least 10 characters long.")
            return render(request, "blogs/blog_registration.html", {"blogs": []})

        # Check if blog name already exists for this user
        if Blog.objects.filter(user=request.user, name=name).exists():
            messages.error(request, f"Blog with name '{name}' already exists!")
            return render(request, "blogs/blog_registration.html", {"blogs": []})

        # Process categories
        categories = [cat.strip() for cat in category_input.split(",") if cat.strip()] if category_input else []
        if len(categories) > 10:
            messages.error(request, "Maximum 10 categories allowed.")
            return render(request, "blogs/blog_registration.html", {"blogs": []})
        
        for cat in categories:
            if len(cat) > 50:
                messages.error(request, "Each category must be 50 characters or less.")
                return render(request, "blogs/blog_registration.html", {"blogs": []})
        
        try:
            blog = Blog.objects.create(
                user=request.user,
                name=name,
                url=url,
                username=username,
                apikey=apikey,
                category=categories
            )
            messages.success(request, f"Blog '{blog.name}' registered successfully!")
            return redirect("blog_registration")
        except Exception as e:
            messages.error(request, f'Error creating blog: {str(e)}')
    
    blogs = Blog.objects.filter(user=request.user)
    return render(request, "blogs/blog_registration.html", {"blogs": blogs})

@admin_required
def blog_edit(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, user=request.user)
    
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        url = request.POST.get("url", "").strip()
        username = request.POST.get("username", "").strip()
        apikey = request.POST.get("apikey", "").strip()
        category_input = request.POST.get("category", "").strip()
        
        # Validation
        if not all([name, url, username, apikey]):
            messages.error(request, "All fields are required!")
            return render(request, "blogs/blog_edit.html", {"blog": blog})
        
        if len(name) < 2:
            messages.error(request, "Blog name must be at least 2 characters long.")
            return render(request, "blogs/blog_edit.html", {"blog": blog})
        
        if not url.startswith(('http://', 'https://')):
            messages.error(request, "URL must start with http:// or https://")
            return render(request, "blogs/blog_edit.html", {"blog": blog})

        if len(username) < 2:
            messages.error(request, "Username must be at least 2 characters long.")
            return render(request, "blogs/blog_edit.html", {"blog": blog})

        if len(apikey) < 10:
            messages.error(request, "API key must be at least 10 characters long.")
            return render(request, "blogs/blog_edit.html", {"blog": blog})

        # Check if new name conflicts with existing blogs (excluding current blog)
        if Blog.objects.filter(user=request.user, name=name).exclude(id=blog_id).exists():
            messages.error(request, f"Blog with name '{name}' already exists!")
            return render(request, "blogs/blog_edit.html", {"blog": blog})

        # Process categories
        categories = [cat.strip() for cat in category_input.split(",") if cat.strip()] if category_input else []
        if len(categories) > 10:
            messages.error(request, "Maximum 10 categories allowed.")
            return render(request, "blogs/blog_edit.html", {"blog": blog})
        
        for cat in categories:
            if len(cat) > 50:
                messages.error(request, "Each category must be 50 characters or less.")
                return render(request, "blogs/blog_edit.html", {"blog": blog})
        
        try:
            blog.name = name
            blog.url = url
            blog.username = username
            blog.apikey = apikey
            blog.category = categories
            blog.save()
            
            messages.success(request, f"Blog '{blog.name}' updated successfully!")
            return redirect("blog_registration")
        except Exception as e:
            messages.error(request, f'Error updating blog: {str(e)}')

    return render(request, "blogs/blog_edit.html", {"blog": blog})

@admin_required
def blog_delete(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, user=request.user)
    
    if request.method == "POST":
        blog_name = blog.name
        blog.delete()
        messages.success(request, f"Blog '{blog_name}' deleted successfully!")
        return redirect("blog_registration")
    
    return render(request, "blogs/blog_delete.html", {"blog": blog})

@admin_required
def article_creation(request):
    if request.method == "POST":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return handle_ai_generation(request)
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        status = request.POST.get("status", "draft")
        blog_id = request.POST.get("blog", "")
        
        # Validation
        if not all([title, content, blog_id]):
            messages.error(request, "Title, content, and blog are required!")
            blogs = Blog.objects.filter(user=request.user)
            form = {"fields": {"blog": {"queryset": blogs}}}
            return render(request, "article_creation.html", {"form": form})
        
        if len(title) < 5:
            messages.error(request, "Title must be at least 5 characters long.")
            blogs = Blog.objects.filter(user=request.user)
            form = {"fields": {"blog": {"queryset": blogs}}}
            return render(request, "article_creation.html", {"form": form})
        
        
        if len(content) < 50:
            messages.error(request, "Content must be at least 50 characters long.")
            blogs = Blog.objects.filter(user=request.user)
            form = {"fields": {"blog": {"queryset": blogs}}}
            return render(request, "article_creation.html", {"form": form})
        
        if len(content.split()) < 10:
            messages.error(request, "Content must contain at least 10 words.")
            blogs = Blog.objects.filter(user=request.user)
            form = {"fields": {"blog": {"queryset": blogs}}}
            return render(request, "article_creation.html", {"form": form})
        
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
        except Blog.DoesNotExist:
            messages.error(request, "Invalid blog selected.")
            blogs = Blog.objects.filter(user=request.user)
            form = {"fields": {"blog": {"queryset": blogs}}}
            return render(request, "article_creation.html", {"form": form})
        
        try:
            article = Article.objects.create(
                user=request.user,
                blog=blog,
                title=title,
                content=content,
                status=status
            )
            messages.success(request, f"Article '{article.title}' created successfully!")
            return redirect("article_list")
        except Exception as e:
            messages.error(request, f'Error creating article: {str(e)}')
    
    # GET request - show the form
    blogs = Blog.objects.filter(user=request.user)
    form = {"fields": {"blog": {"queryset": blogs}}}
    return render(request, "article_creation.html", {"form": form})

@admin_required
def handle_ai_generation(request):
    """Handle AJAX request for AI article generation using Gemini"""
    try:
        data = json.loads(request.body)
        keyword = data.get('keyword', '').strip()
        blog_id = data.get('blog_id', '')
        
        if not keyword:
            return JsonResponse({
                'success': False,
                'error': 'Keyword is required for article generation.'
            })
        
        blog_categories = []
        if blog_id:
            try:
                blog = Blog.objects.get(id=blog_id, user=request.user)
                blog_categories = blog.category if blog.category else []
            except Blog.DoesNotExist:
                pass
        gemini_service = GeminiService()
        result = gemini_service.generate_article(keyword, blog_categories)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })

@admin_required
def article_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id, user=request.user)
    
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        status = request.POST.get("status", "draft")
        blog_id = request.POST.get("blog", "")
        
        # Validation
        if not all([title, content, blog_id]):
            messages.error(request, "Title, content, and blog are required!")
            return render(request, "articles/article_edit.html", {"article": article, "form": None})
        
        if len(title) < 5:
            messages.error(request, "Title must be at least 5 characters long.")
            return render(request, "articles/article_edit.html", {"article": article, "form": None})

        if len(content) < 50:
            messages.error(request, "Content must be at least 50 characters long.")
            return render(request, "articles/article_edit.html", {"article": article, "form": None})
        
        if len(content.split()) < 10:
            messages.error(request, "Content must contain at least 10 words.")
            return render(request, "articles/article_edit.html", {"article": article, "form": None})
        
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
        except Blog.DoesNotExist:
            messages.error(request, "Invalid blog selected.")
            return render(request, "articles/article_edit.html", {"article": article, "form": None})
        
        try:
            article.title = title
            article.content = content
            article.status = status
            article.blog = blog
            article.save()
            
            messages.success(request, f"Article '{article.title}' updated successfully!")
            return redirect("article_list")
        except Exception as e:
            messages.error(request, f'Error updating article: {str(e)}')
    
    # Create a simple form context for the template
    blogs = Blog.objects.filter(user=request.user)
    form = {"fields": {"blog": {"queryset": blogs}}}
    return render(request, "articles/article_edit.html", {"article": article, "form": form})

@admin_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id, user=request.user)
    
    if request.method == "POST":
        article_title = article.title
        article.delete()
        messages.success(request, f"Article '{article_title}' deleted successfully!")
        return redirect("article_list")
    
    return render(request, "articles/article_delete.html", {"article": article})

def article_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, "articles/article_view.html", {"article": article})

@admin_required
def article_list(request):
    articles = Article.objects.filter(user=request.user)
    return render(request, "articles/article_list.html", {"articles": articles})

@admin_required
def admin_panel(request):
    return render(request, "admin_panel.html")

@admin_required
def user_list(request):
    """List all users with their roles"""
    users = User.objects.select_related('profile').filter(is_superuser=False).order_by('date_joined')
    return render(request, "user_management/user_list.html", {"users": users})

@admin_required
def user_create(request):
    """Create a new user"""
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'user')
        
        # Validation
        if not all([username, email, password1, password2]):
            messages.error(request, 'All fields are required!')
            return render(request, 'user_management/user_create.html')
        
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'user_management/user_create.html')
        
        if not username.isalnum():
            messages.error(request, 'Username must contain only letters and numbers.')
            return render(request, 'user_management/user_create.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'user_management/user_create.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'user_management/user_create.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'user_management/user_create.html')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'user_management/user_create.html')

        if role not in ['user', 'admin']:
            messages.error(request, 'Invalid role selected.')
            return render(request, 'user_management/user_create.html')

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.profile.role = role
            user.profile.save()
            
            messages.success(request, f'User {user.username} created successfully with {role} role!')
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')

    return render(request, 'user_management/user_create.html')

@admin_required
def user_edit(request, user_id):
    """Edit user information and role"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not all([username, email]):
            messages.error(request, 'Username and email are required!')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})
        
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})
        
        if not username.isalnum():
            messages.error(request, 'Username must contain only letters and numbers.')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})

        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})
        
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})

        if role not in ['user', 'admin']:
            messages.error(request, 'Invalid role selected.')
            return render(request, 'user_management/user_edit.html', {"user_obj": user})

        try:
            user.username = username
            user.email = email
            user.is_active = is_active
            user.save()
            
            # Update profile role
            user.profile.role = role
            user.profile.save()
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')

    return render(request, 'user_management/user_edit.html', {"user_obj": user})

@admin_required
def user_delete(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting superuser
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('user_list')
    
    # Prevent deleting self
    if user == request.user:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('user_list')
    
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('user_list')

    return render(request, 'user_management/user_delete.html', {"user_obj": user})