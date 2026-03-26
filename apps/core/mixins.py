from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class SuperuserRequiredMixin(LoginRequiredMixin):
    """Allow access only to Django superusers."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Allow access to Admin role and Superuser."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_admin() or request.user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AuthorRequiredMixin(LoginRequiredMixin):
    """Allow access to Author, Admin, and Superuser."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.can_write():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
