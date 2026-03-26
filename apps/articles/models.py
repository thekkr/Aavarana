import bleach
from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.html import strip_tags

from apps.core.models import TimeStampedModel

# Tags and attributes allowed in article body (covers all TinyMCE output)
ALLOWED_TAGS = [
    'p', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 'u', 's', 'del', 'ins', 'mark', 'sub', 'sup',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
    'div', 'span',
]
ALLOWED_ATTRIBUTES = {
    'a':   ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
    'td':  ['colspan', 'rowspan', 'style'],
    'th':  ['colspan', 'rowspan', 'style'],
    'p':   ['style'],
    'div': ['style'],
    'span':['style'],
    'pre': ['class'],
    'code':['class'],
    'table': ['style'],
    'tr':  ['style'],
}


class Category(TimeStampedModel):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Article(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        IN_REVIEW = 'in_review', 'In Review'
        REVISION  = 'revision',  'Revision'
        PUBLISHED = 'published', 'Published'

    title        = models.CharField(max_length=300)
    slug         = models.SlugField(max_length=300, unique=True)
    author       = models.ForeignKey(
                       settings.AUTH_USER_MODEL,
                       on_delete=models.SET_NULL,
                       null=True,
                       related_name='articles',
                   )
    category     = models.ForeignKey(
                       Category,
                       on_delete=models.SET_NULL,
                       null=True, blank=True,
                       related_name='articles',
                   )
    tags         = models.ManyToManyField(Tag, blank=True, related_name='articles')
    cover_image  = models.ImageField(upload_to='articles/', blank=True)
    excerpt      = models.TextField(blank=True, max_length=300)
    body         = models.TextField()
    read_time    = models.PositiveIntegerField(default=0)
    status       = models.CharField(
                       max_length=10,
                       choices=Status.choices,
                       default=Status.DRAFT,
                       db_index=True,
                   )
    published_at      = models.DateTimeField(null=True, blank=True)
    view_count        = models.PositiveIntegerField(default=0)
    submission_count  = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes  = [models.Index(fields=['status', '-published_at'])]

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.body = bleach.clean(self.body, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
            plain = strip_tags(self.body)
            self.read_time = max(1, round(len(plain.split()) / 200))
            if not self.excerpt:
                words = plain.split()[:30]
                self.excerpt = ' '.join(words) + ('...' if len(plain.split()) > 30 else '')
        super().save(*args, **kwargs)

    def submit_for_review(self):
        self.status = self.Status.IN_REVIEW
        self.save(update_fields=['status', 'updated_at'])
        Article.objects.filter(pk=self.pk).update(
            submission_count=F('submission_count') + 1
        )

    def publish(self):
        self.status      = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def send_to_revision(self):
        self.status = self.Status.REVISION
        self.save(update_fields=['status', 'updated_at'])

    def increment_views(self):
        Article.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)

    def is_editable_by(self, user):
        if self.status in (self.Status.DRAFT, self.Status.REVISION):
            return user == self.author or user.is_admin()
        return False

    def is_deletable_by(self, user):
        if self.status == self.Status.PUBLISHED:
            return user.is_admin()
        return user == self.author or user.is_admin()

    def __str__(self):
        return self.title


class ReviewNote(TimeStampedModel):
    class Action(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    article  = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='review_notes')
    reviewer = models.ForeignKey(
                   settings.AUTH_USER_MODEL,
                   on_delete=models.SET_NULL,
                   null=True,
                   related_name='review_notes',
               )
    note     = models.TextField(blank=True)
    action   = models.CharField(max_length=10, choices=Action.choices)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} by {self.reviewer} on {self.article}'


class Like(TimeStampedModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    user    = models.ForeignKey(
                  settings.AUTH_USER_MODEL,
                  on_delete=models.CASCADE,
                  related_name='likes',
              )

    class Meta:
        unique_together = ('article', 'user')

    def __str__(self):
        return f'{self.user} likes {self.article}'


class SavedArticle(TimeStampedModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='saves')
    user    = models.ForeignKey(
                  settings.AUTH_USER_MODEL,
                  on_delete=models.CASCADE,
                  related_name='saved_articles',
              )

    class Meta:
        unique_together = ('article', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} saved {self.article}'


class Comment(TimeStampedModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author  = models.ForeignKey(
                  settings.AUTH_USER_MODEL,
                  on_delete=models.SET_NULL,
                  null=True,
                  related_name='comments',
              )
    body    = models.TextField(max_length=2000)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.article}'
