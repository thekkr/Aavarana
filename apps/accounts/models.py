from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        AUTHOR = 'author', 'Author'
        ADMIN  = 'admin',  'Admin'

    email        = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role         = models.CharField(
                       max_length=10,
                       choices=Role.choices,
                       default=Role.VIEWER,
                       db_index=True,
                   )

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_author(self):
        return self.role == self.Role.AUTHOR

    def is_viewer(self):
        return self.role == self.Role.VIEWER

    def can_write(self):
        return self.role in (self.Role.AUTHOR, self.Role.ADMIN)

    def is_newsletter_subscribed(self):
        return NewsletterSubscriber.objects.filter(user=self).exists()

    @property
    def profile(self):
        obj, _ = Profile.objects.get_or_create(user=self)
        return obj

    def __str__(self):
        return self.username


class Profile(TimeStampedModel):
    DEFAULT_AVATAR_CHOICES = [
        ('felix',   'Felix'),
        ('luna',    'Luna'),
        ('max',     'Max'),
        ('zoe',     'Zoe'),
        ('alex',    'Alex'),
        ('taylor',  'Taylor'),
        ('jordan',  'Jordan'),
        ('casey',   'Casey'),
        ('river',   'River'),
        ('sage',    'Sage'),
    ]

    user           = models.OneToOneField(
                         settings.AUTH_USER_MODEL,
                         on_delete=models.CASCADE,
                         related_name='_profile',
                     )
    avatar         = models.ImageField(upload_to='avatars/', blank=True)
    default_avatar = models.CharField(
                         max_length=50,
                         blank=True,
                         choices=DEFAULT_AVATAR_CHOICES,
                     )
    bio     = models.TextField(blank=True, max_length=500)
    website = models.URLField(blank=True)

    def get_avatar_url(self):
        """Return the URL to display as this profile's avatar."""
        if self.avatar:
            return self.avatar.url
        if self.default_avatar:
            return f'https://api.dicebear.com/9.x/thumbs/svg?seed={self.default_avatar}'
        return None

    def __str__(self):
        return f'Profile of {self.user.email}'


class NewsletterSubscriber(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='newsletter_subscription',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} (subscribed {self.created_at.date()})'
