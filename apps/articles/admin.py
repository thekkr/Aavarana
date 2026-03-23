from django.contrib import admin
from .models import Article, Category, Tag, Comment, ReviewNote, Like


class ReviewNoteInline(admin.TabularInline):
    model = ReviewNote
    extra = 0
    readonly_fields = ["reviewer", "action", "note", "created_at"]
    can_delete = False


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ["author", "body", "created_at"]
    can_delete = True


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "read_time", "view_count", "published_at"]
    list_filter = ["status", "category", "tags"]
    search_fields = ["title", "body", "author__email"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    inlines = [ReviewNoteInline, CommentInline]
    actions = ["make_published", "make_draft"]

    def make_published(self, request, queryset):
        queryset.update(status="published")
    make_published.short_description = "Mark selected as published"

    def make_draft(self, request, queryset):
        queryset.update(status="draft")
    make_draft.short_description = "Mark selected as draft"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "slug"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "slug"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "article", "created_at"]
    search_fields = ["author__email", "body"]


@admin.register(ReviewNote)
class ReviewNoteAdmin(admin.ModelAdmin):
    list_display = ["article", "reviewer", "action", "created_at"]
    list_filter = ["action"]
