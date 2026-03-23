from django.urls import path
from .views import (
    ArticleListView, MyArticlesView, ArticleDetailView,
    ArticleCreateView, ArticleEditView, ArticleDeleteView, ArticleSubmitView,
    ReviewQueueView, ArticleReviewView,
    LikeToggleView, CommentCreateView, CommentDeleteView,
    SaveToggleView, SavedArticlesView,
    CategoryListView, CategoryDetailView, CategoryCreateView, CategoryEditView, CategoryDeleteView,
    TagDetailView,
    EditorImageUploadView,
)

app_name = "articles"

urlpatterns = [
    path("", ArticleListView.as_view(), name="list"),
    path("my/", MyArticlesView.as_view(), name="my_articles"),
    path("saved/", SavedArticlesView.as_view(), name="saved_articles"),
    path("create/", ArticleCreateView.as_view(), name="create"),
    path("review/", ReviewQueueView.as_view(), name="review_queue"),
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("categories/add/", CategoryCreateView.as_view(), name="category_create"),
    path("category/<slug:slug>/edit/", CategoryEditView.as_view(), name="category_edit"),
    path("category/<slug:slug>/delete/", CategoryDeleteView.as_view(), name="category_delete"),
    path("category/<slug:slug>/", CategoryDetailView.as_view(), name="category_detail"),
    path("tag/<slug:slug>/", TagDetailView.as_view(), name="tag_detail"),
    path("comment/<int:pk>/delete/", CommentDeleteView.as_view(), name="comment_delete"),
    path("<slug:slug>/", ArticleDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", ArticleEditView.as_view(), name="edit"),
    path("<slug:slug>/delete/", ArticleDeleteView.as_view(), name="delete"),
    path("<slug:slug>/submit/", ArticleSubmitView.as_view(), name="submit"),
    path("<slug:slug>/review/", ArticleReviewView.as_view(), name="review"),
    path("<slug:slug>/like/", LikeToggleView.as_view(), name="like"),
    path("<slug:slug>/save/", SaveToggleView.as_view(), name="save"),
    path("<slug:slug>/comment/", CommentCreateView.as_view(), name="comment_create"),
    path("editor/upload-image/", EditorImageUploadView.as_view(), name="editor_image_upload"),
]
