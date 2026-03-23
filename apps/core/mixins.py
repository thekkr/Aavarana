from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """Allow access only to Admin role."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AuthorRequiredMixin(LoginRequiredMixin):
    """Allow access only to Author and Admin roles."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.can_write():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
