from .base import *

DEBUG = False

# HTTPS enforcement
SECURE_SSL_REDIRECT            = True
SECURE_HSTS_SECONDS            = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True

# Secure cookies
SESSION_COOKIE_SECURE   = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE      = True
CSRF_COOKIE_HTTPONLY    = True

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF  = True
SECURE_REFERRER_POLICY       = 'strict-origin-when-cross-origin'
PERMISSIONS_POLICY           = 'geolocation=(), microphone=(), camera=()'
X_FRAME_OPTIONS              = 'DENY'
