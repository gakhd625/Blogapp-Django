from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.user_register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("blog-registration/", views.blog_registration, name="blog_registration"),
    path("blog-edit/<int:blog_id>/", views.blog_edit, name="blog_edit"),
    path("blog-delete/<int:blog_id>/", views.blog_delete, name="blog_delete"),
    path("blog-view/<int:id>/", views.blog_view, name="blog_view"),
    path("article-creation/", views.article_creation, name="article_creation"),
    path("article-edit/<int:article_id>/", views.article_edit, name="article_edit"),
    path("article-delete/<int:article_id>/", views.article_delete, name="article_delete"),
    path("article-list/", views.article_list, name="article_list"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
]
