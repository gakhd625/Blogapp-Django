from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from .models import Blog, Article

# blogs = [
#     {"name": "Rakurin's Blog", "url": "https://rakurin.net/blog/", "username": "ra781228", "apikey": "********", "category": ["HELLOW WORLD"]},
# ]

# articles = [
#     {"title": "How to Write a Blog with AI", "date": "2024-06-01 10:00", "status": "Published"},
#     {"title": "SEO-Friendly Article Structure", "date": "2024-06-01 09:30", "status": "Draft"}
# ]


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

# Main Views
def home(request):
    return render(request, "home.html")

@login_required
def blog_view(request, id):
    blog = Blog.objects.filter(id=id, user=request.user).first()
    articles = Article.objects.filter(blog_id=id, user=request.user)
    return render(request, "blog_view.html", {"blog": blog, "articles": articles})  

@login_required
def blog_registration(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        url = request.POST.get("url", "").strip()
        username = request.POST.get("username", "").strip()
        apikey = request.POST.get("apikey", "").strip()
        category_input = request.POST.get("category", "").strip()
        if not all([name, url, username, apikey]):
            messages.error(request, "All fields are required!")
            return render(request, "blog_registration.html", {"blogs": []})
        
        if len(name) < 2:
            messages.error(request, "Blog name must be at least 2 characters long.")
            return render(request, "blog_registration.html", {"blogs": []})
        
        if not url.startswith(('http://', 'https://', 'www.')):
            messages.error(request, "URL must start with http:// or https:// or www.")
            return render(request, "blog_registration.html", {"blogs": []})
        
        if len(username) < 2:
            messages.error(request, "Username must be at least 2 characters long.")
            return render(request, "blog_registration.html", {"blogs": []})
        
        if len(apikey) < 10:
            messages.error(request, "API key must be at least 10 characters long.")
            return render(request, "blog_registration.html", {"blogs": []})
        
        # Check if blog name already exists for this user
        if Blog.objects.filter(user=request.user, name=name).exists():
            messages.error(request, f"Blog with name '{name}' already exists!")
            return render(request, "blog_registration.html", {"blogs": []})
        
        # Process categories
        categories = [cat.strip() for cat in category_input.split(",") if cat.strip()] if category_input else []
        if len(categories) > 10:
            messages.error(request, "Maximum 10 categories allowed.")
            return render(request, "blog_registration.html", {"blogs": []})
        
        for cat in categories:
            if len(cat) > 50:
                messages.error(request, "Each category must be 50 characters or less.")
                return render(request, "blog_registration.html", {"blogs": []})
        
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
    return render(request, "blog_registration.html", {"blogs": blogs})

@login_required
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
            return render(request, "blog_edit.html", {"blog": blog})
        
        if len(name) < 2:
            messages.error(request, "Blog name must be at least 2 characters long.")
            return render(request, "blog_edit.html", {"blog": blog})
        
        if not url.startswith(('http://', 'https://')):
            messages.error(request, "URL must start with http:// or https://")
            return render(request, "blog_edit.html", {"blog": blog})
        
        if len(username) < 2:
            messages.error(request, "Username must be at least 2 characters long.")
            return render(request, "blog_edit.html", {"blog": blog})
        
        if len(apikey) < 10:
            messages.error(request, "API key must be at least 10 characters long.")
            return render(request, "blog_edit.html", {"blog": blog})
        
        # Check if new name conflicts with existing blogs (excluding current blog)
        if Blog.objects.filter(user=request.user, name=name).exclude(id=blog_id).exists():
            messages.error(request, f"Blog with name '{name}' already exists!")
            return render(request, "blog_edit.html", {"blog": blog})
        
        # Process categories
        categories = [cat.strip() for cat in category_input.split(",") if cat.strip()] if category_input else []
        if len(categories) > 10:
            messages.error(request, "Maximum 10 categories allowed.")
            return render(request, "blog_edit.html", {"blog": blog})
        
        for cat in categories:
            if len(cat) > 50:
                messages.error(request, "Each category must be 50 characters or less.")
                return render(request, "blog_edit.html", {"blog": blog})
        
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
    
    return render(request, "blog_edit.html", {"blog": blog})

@login_required
def blog_delete(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, user=request.user)
    
    if request.method == "POST":
        blog_name = blog.name
        blog.delete()
        messages.success(request, f"Blog '{blog_name}' deleted successfully!")
        return redirect("blog_registration")
    
    return render(request, "blog_delete.html", {"blog": blog})

@login_required
def article_creation(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        status = request.POST.get("status", "draft")
        blog_id = request.POST.get("blog", "")
        
        # Validation
        if not all([title, content, blog_id]):
            messages.error(request, "Title, content, and blog are required!")
            return render(request, "article_creation.html", {"form": None})
        
        if len(title) < 5:
            messages.error(request, "Title must be at least 5 characters long.")
            return render(request, "article_creation.html", {"form": None})
        
        if not title.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            messages.error(request, "Title can only contain letters, numbers, spaces, hyphens, and underscores.")
            return render(request, "article_creation.html", {"form": None})
        
        if len(content) < 50:
            messages.error(request, "Content must be at least 50 characters long.")
            return render(request, "article_creation.html", {"form": None})
        
        if len(content.split()) < 10:
            messages.error(request, "Content must contain at least 10 words.")
            return render(request, "article_creation.html", {"form": None})
        
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
        except Blog.DoesNotExist:
            messages.error(request, "Invalid blog selected.")
            return render(request, "article_creation.html", {"form": None})
        
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
    
    # Create a simple form context for the template
    blogs = Blog.objects.filter(user=request.user)
    form = {"fields": {"blog": {"queryset": blogs}}}
    return render(request, "article_creation.html", {"form": form})

@login_required
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
            return render(request, "article_edit.html", {"article": article, "form": None})
        
        if len(title) < 5:
            messages.error(request, "Title must be at least 5 characters long.")
            return render(request, "article_edit.html", {"article": article, "form": None})
        
        if not title.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            messages.error(request, "Title can only contain letters, numbers, spaces, hyphens, and underscores.")
            return render(request, "article_edit.html", {"article": article, "form": None})
        
        if len(content) < 50:
            messages.error(request, "Content must be at least 50 characters long.")
            return render(request, "article_edit.html", {"article": article, "form": None})
        
        if len(content.split()) < 10:
            messages.error(request, "Content must contain at least 10 words.")
            return render(request, "article_edit.html", {"article": article, "form": None})
        
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
        except Blog.DoesNotExist:
            messages.error(request, "Invalid blog selected.")
            return render(request, "article_edit.html", {"article": article, "form": None})
        
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
    return render(request, "article_edit.html", {"article": article, "form": form})

@login_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id, user=request.user)
    
    if request.method == "POST":
        article_title = article.title
        article.delete()
        messages.success(request, f"Article '{article_title}' deleted successfully!")
        return redirect("article_list")
    
    return render(request, "article_delete.html", {"article": article})

@login_required
def article_list(request):
    articles = Article.objects.filter(user=request.user)
    return render(request, "article_list.html", {"articles": articles})

@login_required
def admin_panel(request):
    return render(request, "admin_panel.html")
