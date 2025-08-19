from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("blog-registration/", views.blog_registration, name="blog_registration"),
    path("blog-edit/<str:blog_name>/", views.blog_edit, name="blog_edit"),
    path("blog-delete/<str:blog_name>/", views.blog_delete, name="blog_delete"),
    path("article-creation/", views.article_creation, name="article_creation"),
    path("article-edit/<int:article_id>/", views.article_edit, name="article_edit"),
    path("article-delete/<int:article_id>/", views.article_delete, name="article_delete"),
    path("article-list/", views.article_list, name="article_list"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("blog-view/", views.blog_view, name="blog_view"),
]
