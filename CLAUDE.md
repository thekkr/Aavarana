# Aavarana — Claude Code Context

## Project Overview

Django 6.0.3 content publishing platform. Three apps: `core`, `accounts`, `articles`.
Bootstrap 5 UI, TinyMCE rich text editor, Google OAuth via django-allauth.

---

## Running the Project

```bash
# Development
cp .env.example .env          # fill in SECRET_KEY at minimum
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Uses aavarana.settings.dev by default (set in manage.py)

# Production
export DJANGO_SETTINGS_MODULE=aavarana.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn aavarana.wsgi:application --bind 0.0.0.0:8000
```

See `DEPLOY.md` for full Gunicorn + Nginx + Cloudflare deployment guide.

---

## Architecture

- **Settings**: Split — `base.py` → `dev.py` / `prod.py`
- **Templates**: All in `/templates/` (not per-app). Partials in `templates/partials/`
- **Base model**: `TimeStampedModel` (in `apps/core/models.py`) — all models inherit this
- **Auth**: Custom `AbstractUser` in `apps/accounts/models.py`. `USERNAME_FIELD = 'username'`

---

## Role & Permission System

| Role | Can do |
|---|---|
| **Viewer** | Read published articles, like, comment, save |
| **Author** | + Create/edit own articles, submit for review |
| **Admin** | + Review/publish articles, manage Viewer↔Author roles. No Django admin access. |
| **Superuser** | Everything + Django admin panel + promote anyone to Admin |

**How to check roles in code:**
```python
user.is_viewer()        # role == 'viewer'
user.is_author()        # role == 'author'
user.is_admin()         # role == 'admin'
user.is_superuser       # Django built-in flag — true Superadmin
user.can_write()        # Author or Admin or Superuser
user.is_google_user()   # registered via Google OAuth
```

**Mixins** (all in `apps/core/mixins.py`):
- `SuperuserRequiredMixin` — `is_superuser` only
- `AdminRequiredMixin` — `is_admin()` or `is_superuser`
- `AuthorRequiredMixin` — `can_write()`

**Important:** Never set `is_staff=True` on the Admin role. Only Superuser gets Django admin access.

---

## Article Workflow

```
Draft → In Review → Published
              ↓
           Revision → In Review (again)
```

**Model methods** (all on `Article`):
- `submit_for_review()` — sets status + increments `submission_count` via `F()`
- `publish()` — sets status + `published_at`
- `send_to_revision()` — sets status back to revision
- `increment_views()` — atomic update via `F()` expression
- `is_editable_by(user)` — draft/revision + author or admin
- `is_deletable_by(user)` — published = admin only; others = author or admin

---

## Key Patterns — Always Follow

### Forms
```django
{# CORRECT — renders fields only, no extra <form> tag #}
{{ form|crispy }}
{{ form.field_name|as_crispy_field }}

{# WRONG — renders its own <form> tag, causes nested forms, breaks submission #}
{% crispy form %}
```

### Counters / Atomic Updates
```python
# CORRECT — atomic, no race condition
Article.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)

# WRONG — race condition under concurrent requests
self.view_count += 1
self.save()
```

### Partial Saves
The `Article.save()` override recalculates `read_time` and `excerpt`. It skips this
when `update_fields` is passed. Always use `update_fields` for status-only saves:
```python
self.save(update_fields=['status', 'updated_at'])  # skips body recalc
```

### Queries — Always Use select_related / prefetch_related
```python
# Article lists
Article.objects.select_related('author', 'category').prefetch_related('tags')

# Profile page — avoids N+1 on profile and social account lookups
CustomUser.objects.select_related('_profile').prefetch_related('socialaccount_set')
```

### AJAX Toggles (Like / Save)
Views check `X-Requested-With: XMLHttpRequest` header and return JSON.
Templates use `fetch()` — never full form POSTs for these actions.

### Notifications / Messages
All Django `messages` render as Bootstrap toasts (bottom-right).
Handled by `templates/partials/_messages.html` — no custom template changes needed.
```python
messages.success(request, 'Article published.')
messages.error(request, 'Something went wrong.')
```

---

## Things to Avoid

- **Never** use `{% crispy form %}` — use `{{ form|crispy }}` instead
- **Never** increment model counters in Python — use `F()` expressions
- **Never** call `user.profile` in a loop — use `select_related('_profile')`
- **Never** add `is_staff=True` to Admin role users
- **Never** hardcode `ALLOWED_HOSTS` — it reads from `.env`
- **Never** commit `.env` or `db.sqlite3` — both in `.gitignore`
- **Never** use `{{ article.body|linebreaks }}` — body is HTML from TinyMCE, use `{{ article.body|safe }}` (bleach sanitizes on save)
- **Never** call `Article.save()` without `update_fields` for status changes — it will recalculate excerpt/read_time unnecessarily

---

## Key Files

| Purpose | File |
|---|---|
| User model + roles | `apps/accounts/models.py` |
| Article model + workflow | `apps/articles/models.py` |
| Permission mixins | `apps/core/mixins.py` |
| Account forms | `apps/accounts/forms.py` |
| Article forms | `apps/articles/forms.py` |
| Account views | `apps/accounts/views.py` |
| Article views | `apps/articles/views.py` |
| Root URLs | `aavarana/urls.py` |
| Account URLs | `apps/accounts/urls.py` |
| Article URLs | `apps/articles/urls.py` |
| Base template | `templates/base.html` |
| Navbar | `templates/partials/_navbar.html` |
| Toast messages | `templates/partials/_messages.html` |
| Base settings | `aavarana/settings/base.py` |

---

## Dependencies

| Package | Purpose |
|---|---|
| `Django==6.0.3` | Framework |
| `bleach==6.2.0` | Sanitize TinyMCE HTML on article save |
| `django-allauth==65.3.0` | Google OAuth + username/password auth |
| `django-crispy-forms==2.6` | Form rendering |
| `crispy-bootstrap5==2026.3` | Bootstrap 5 template pack for crispy |
| `python-decouple==3.8` | Load `.env` variables |
| `Pillow==12.1.1` | Image uploads (avatars, cover images) |

---

## Git & Deploy

- **Remote**: `https://github.com/thekkr/Aavarana.git`
- **Branch**: `main`
- **Deploy**: `DEPLOY.md` — full guide for Gunicorn + Nginx + Cloudflare
- **Production settings**: `aavarana.settings.prod`
- **`.env.example`**: Lists all required environment variables with descriptions
