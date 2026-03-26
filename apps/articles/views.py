import os
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse, reverse_lazy

from apps.core.mixins import AdminRequiredMixin, AuthorRequiredMixin
from .forms import ArticleForm, CategoryForm, ReviewForm, CommentForm
from .models import Article, Category, Tag, Like, Comment, ReviewNote, SavedArticle


class ArticleListView(ListView):
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(
            status='published'
        ).select_related('author', 'category').annotate(
            likes_count=Count('likes')
        ).order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        return ctx


class MyArticlesView(AuthorRequiredMixin, TemplateView):
    template_name = 'articles/my_articles.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        all_articles = Article.objects.filter(author=user).select_related('category').order_by('-updated_at')
        ctx['drafts']    = [a for a in all_articles if a.status == 'draft']
        ctx['in_review'] = [a for a in all_articles if a.status == 'in_review']
        ctx['revisions'] = [a for a in all_articles if a.status == 'revision']
        ctx['published'] = [a for a in all_articles if a.status == 'published']
        return ctx


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Article, slug=self.kwargs['slug'])
        user = self.request.user
        if obj.status != 'published':
            if not user.is_authenticated:
                raise PermissionDenied
            if not (user == obj.author or user.is_admin()):
                raise PermissionDenied
        return obj

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.status == 'published':
            self.object.increment_views()
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['comment_form'] = CommentForm()
        ctx['comments'] = self.object.comments.select_related('author').order_by('created_at')
        ctx['like_count'] = self.object.likes.count()
        if user.is_authenticated and (user == self.object.author or user.is_admin()):
            ctx['review_notes'] = self.object.review_notes.select_related('reviewer')
        else:
            ctx['review_notes'] = []
        ctx['user_liked'] = self.object.likes.filter(user=user).exists() if user.is_authenticated else False
        ctx['user_saved'] = self.object.saves.filter(user=user).exists() if user.is_authenticated else False
        ctx['can_delete'] = user.is_authenticated and self.object.is_deletable_by(user)
        return ctx


class ArticleCreateView(AuthorRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'

    def form_valid(self, form):
        article = form.save(commit=False)
        article.author = self.request.user
        article.status = 'draft'
        article.slug = self._unique_slug(form.cleaned_data['title'])
        article.save()
        form.save_m2m()
        messages.success(self.request, 'Article saved as draft.')
        return redirect('articles:detail', slug=article.slug)

    def _unique_slug(self, title):
        base = slugify(title)
        slug = base
        counter = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f'{base}-{counter}'
            counter += 1
        return slug


class ArticleEditView(AuthorRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Article, slug=self.kwargs['slug'])
        if not obj.is_editable_by(self.request.user):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        return reverse('articles:detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        messages.success(self.request, 'Article updated.')
        return super().form_valid(form)


class ArticleDeleteView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        if not article.is_deletable_by(request.user):
            raise PermissionDenied
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('articles:my_articles')


class ArticleSubmitView(AuthorRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, author=request.user)
        if article.status not in ('draft', 'revision'):
            messages.error(request, 'Article cannot be submitted in its current state.')
            return redirect('articles:detail', slug=slug)
        article.submit_for_review()
        messages.success(request, 'Article submitted for review.')
        return redirect('articles:detail', slug=slug)


class ReviewQueueView(AdminRequiredMixin, ListView):
    template_name = 'articles/review_queue.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Article.objects.filter(
            status='in_review'
        ).select_related('author').order_by('updated_at')


class ArticleReviewView(AdminRequiredMixin, View):
    template_name = 'articles/article_review.html'

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='in_review')
        form = ReviewForm()
        return render(request, self.template_name, {
            'article': article,
            'form': form,
            'review_notes': article.review_notes.select_related('reviewer'),
        })

    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='in_review')
        form = ReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            note = form.cleaned_data.get('note', '').strip()
            ReviewNote.objects.create(
                article=article, reviewer=request.user,
                action=action, note=note,
            )
            if action == 'approved':
                article.publish()
                messages.success(request, f'"{article.title}" has been published.')
            else:
                article.send_to_revision()
                messages.info(request, f'"{article.title}" sent back for revision.')
            return redirect('articles:review_queue')
        return render(request, self.template_name, {
            'article': article,
            'form': form,
            'review_notes': article.review_notes.select_related('reviewer'),
        })


class LikeToggleView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='published')
        if article.author == request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'You cannot like your own article.'}, status=403)
            messages.error(request, 'You cannot like your own article.')
            return redirect('articles:detail', slug=slug)
        like, created = Like.objects.get_or_create(article=article, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        count = article.likes.count()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'liked': liked, 'count': count})
        return redirect('articles:detail', slug=slug)


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='published')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment posted.')
        return redirect('articles:detail', slug=slug)


class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment.objects.select_related('article'), pk=pk)
        if comment.author != request.user and not request.user.is_admin():
            raise PermissionDenied
        slug = comment.article.slug
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect('articles:detail', slug=slug)


class SaveToggleView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='published')
        save, created = SavedArticle.objects.get_or_create(article=article, user=request.user)
        if not created:
            save.delete()
            saved = False
        else:
            saved = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'saved': saved})
        return redirect('articles:detail', slug=slug)


class SavedArticlesView(LoginRequiredMixin, ListView):
    template_name = 'articles/saved_articles.html'
    context_object_name = 'saved'
    paginate_by = 12

    def get_queryset(self):
        return SavedArticle.objects.filter(
            user=self.request.user
        ).select_related('article', 'article__author', 'article__category')


class CategoryListView(ListView):
    model = Category
    template_name = 'articles/category_list.html'
    context_object_name = 'categories'


class CategoryDetailView(ListView):
    template_name = 'articles/category_detail.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Article.objects.filter(
            category=self.category, status='published'
        ).select_related('author', 'category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        return ctx


class TagDetailView(ListView):
    template_name = 'articles/tag_detail.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Article.objects.filter(
            tags=self.tag, status='published'
        ).select_related('author', 'category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tag'] = self.tag
        return ctx


class EditorImageUploadView(AuthorRequiredMixin, View):
    """Accepts image uploads from TinyMCE and returns the hosted URL."""

    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)

        if file.content_type not in self.ALLOWED_MIME_TYPES:
            return JsonResponse({'error': 'Unsupported file type'}, status=400)

        # Read first 12 bytes to verify magic bytes match claimed type
        header = file.read(12)
        file.seek(0)
        magic = {
            b'\xff\xd8\xff': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'RIFF': 'image/webp',
        }
        verified = any(header.startswith(sig) for sig in magic)
        if not verified:
            return JsonResponse({'error': 'File content does not match image type'}, status=400)

        path = default_storage.save(f'editor/{file.name}', file)
        url  = request.build_absolute_uri(default_storage.url(path))
        # TinyMCE expects: { "location": "<url>" }
        return JsonResponse({'location': url})


class CategoryCreateView(AdminRequiredMixin, CreateView):
    model         = Category
    form_class    = CategoryForm
    template_name = 'articles/category_form.html'
    success_url   = reverse_lazy('articles:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created.')
        return super().form_valid(form)


class CategoryEditView(AdminRequiredMixin, UpdateView):
    model         = Category
    form_class    = CategoryForm
    template_name = 'articles/category_form.html'
    success_url   = reverse_lazy('articles:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated.')
        return super().form_valid(form)


class CategoryDeleteView(AdminRequiredMixin, View):
    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('articles:category_list')
