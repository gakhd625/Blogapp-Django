from django.shortcuts import render, redirect
from django.http import Http404

# In-memory storage (like in Flask)
blogs = [
    {"name": "Rakurin's Blog", "url": "https://rakurin.net/blog/", "username": "ra781228", "apikey": "********", "category": ["HELLOW WORLD"]},
]

articles = [
    {"title": "How to Write a Blog with AI", "date": "2024-06-01 10:00", "status": "Published"},
    {"title": "SEO-Friendly Article Structure", "date": "2024-06-01 09:30", "status": "Draft"}
]

# Views
def home(request):
    return render(request, "home.html")

def blog_registration(request):
    if request.method == "POST":
        blogs.append({
            "name": request.POST.get("name"),
            "url": request.POST.get("url"),
            "username": request.POST.get("username"),
            "apikey": request.POST.get("apikey"),
            "category": request.POST.getlist("category")
        })
        return redirect("blog_registration")
    return render(request, "blog_registration.html", {"blogs": blogs})

def blog_edit(request, blog_name):
    blog = next((b for b in blogs if b["name"] == blog_name), None)
    if not blog:
        return redirect("blog_registration")
    
    if request.method == "POST":
        blog["name"] = request.POST.get("name")
        blog["url"] = request.POST.get("url")
        blog["username"] = request.POST.get("username")
        blog["apikey"] = request.POST.get("apikey")
        blog["category"] = request.POST.getlist("category")
        return redirect("blog_registration")
    return render(request, "blog_edit.html", {"blog": blog})

def blog_delete(request, blog_name):
    blog = next((b for b in blogs if b["name"] == blog_name), None)
    if not blog:
        return redirect("blog_registration")
    
    if request.method == "POST":
        blogs.remove(blog)
        return redirect("blog_registration")
    return render(request, "blog_delete.html", {"blog": blog})

def article_creation(request):
    return render(request, "article_creation.html", {"blogs": blogs})

def article_edit(request, article_id):
    if article_id < 0 or article_id >= len(articles):
        raise Http404("Article not found")
    
    if request.method == "POST":
        articles[article_id]["title"] = request.POST.get("title")
        articles[article_id]["content"] = request.POST.get("content")
        return redirect("article_list")
    return render(request, "article_edit.html", {"article": articles[article_id]})

def article_delete(request, article_id):
    if 0 <= article_id < len(articles):
        articles.pop(article_id)
    return redirect("article_list")

def article_list(request):
    return render(request, "article_list.html", {"articles": articles})

def admin_panel(request):
    return render(request, "admin_panel.html")
