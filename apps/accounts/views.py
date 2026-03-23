from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView, ListView, FormView, TemplateView

from apps.core.mixins import AdminRequiredMixin
from .forms import RegisterForm, ProfileEditForm, RoleChangeForm, PasswordResetRequestForm
from .models import CustomUser, Profile, NewsletterSubscriber


class CustomPasswordResetView(FormView):
    """Show reset link directly on the site — no email needed (email wired in later)."""
    template_name = 'accounts/password_reset.html'
    form_class    = PasswordResetRequestForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse('accounts:password_reset_confirm',
                        kwargs={'uidb64': uid, 'token': token})
            )
            self.request.session['password_reset_link'] = reset_url
        except CustomUser.DoesNotExist:
            # Don't reveal whether the email exists
            self.request.session.pop('password_reset_link', None)
        return redirect('accounts:password_reset_done')


class PasswordResetDoneSiteView(TemplateView):
    """Display the on-site reset link after the form is submitted."""
    template_name = 'accounts/password_reset_done.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reset_link'] = self.request.session.pop('password_reset_link', None)
        return ctx


class RegisterView(CreateView):
    form_class    = RegisterForm
    template_name = 'accounts/register.html'
    success_url   = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome, {user.first_name or user.email}!')
        return redirect(self.success_url)


class ProfileView(DetailView):
    model               = CustomUser
    template_name       = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field          = 'username'
    slug_url_kwarg      = 'username'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.articles.models import Article
        ctx['articles'] = Article.objects.filter(
            author=self.object, status='published'
        ).select_related('category').order_by('-published_at')[:5]
        return ctx


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model         = Profile
    form_class    = ProfileEditForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['avatar_choices'] = Profile.DEFAULT_AVATAR_CHOICES
        return ctx

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


class NewsletterSubscribeView(LoginRequiredMixin, View):
    def get(self, request):
        """Handle redirect here after login via ?next=."""
        NewsletterSubscriber.objects.get_or_create(user=request.user)
        messages.success(request, 'You are now subscribed to the Aavarana newsletter!')
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))

    def post(self, request):
        NewsletterSubscriber.objects.get_or_create(user=request.user)
        messages.success(request, 'You are now subscribed to the Aavarana newsletter!')
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))


class UserListView(AdminRequiredMixin, ListView):
    model               = CustomUser
    template_name       = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by         = 20
    ordering            = ['-date_joined']

    def get_queryset(self):
        return CustomUser.objects.exclude(role='admin').order_by('-date_joined')


class UserRoleUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        target_user = get_object_or_404(CustomUser, pk=pk)

        # Safety checks
        if target_user == request.user:
            messages.error(request, 'You cannot change your own role.')
            return redirect('accounts:user_list')
        if target_user.is_admin():
            messages.error(request, 'Cannot change another admin\'s role.')
            return redirect('accounts:user_list')

        form = RoleChangeForm(request.POST)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            target_user.role = new_role
            target_user.save(update_fields=['role'])
            messages.success(
                request,
                f'{target_user.email} is now a {target_user.get_role_display()}.'
            )
        else:
            messages.error(request, 'Invalid role selection.')

        return redirect('accounts:user_list')
