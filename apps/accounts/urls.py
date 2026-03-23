from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.urls import path, reverse_lazy

from .views import (
    RegisterView, ProfileView, ProfileEditView,
    UserListView, UserRoleUpdateView,
    CustomPasswordResetView, PasswordResetDoneSiteView,
    NewsletterSubscribeView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),

    path('newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),

    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user_role_update'),

    # Password reset (on-site link — no email required)
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneSiteView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
]
