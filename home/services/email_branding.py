"""Contexto visual partilhado pelos emails transacionais da loja."""

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


def contexto_email_base() -> dict:
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    logo_path = staticfiles_storage.url("home/img/logo.jpg")
    if logo_path.startswith("http"):
        logo_url = logo_path
    else:
        logo_url = f"{site_url}/{logo_path.lstrip('/')}"

    return {
        "site_nome": "Mesa Brasileira",
        "site_url": site_url,
        "site_tagline": "Em respeito ao nosso samba",
        "logo_url": logo_url,
        "cor_brown": "#4b3621",
        "cor_brown_muted": "#6b5344",
        "cor_cream": "#e6d5b8",
        "cor_cream_light": "#f5f0e6",
        "cor_card": "#faf6ef",
        "cor_green": "#009739",
        "cor_yellow": "#ffcc29",
        "cor_blue": "#002776",
        "cor_border": "#d4c4a8",
    }
