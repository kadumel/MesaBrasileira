"""
Busca miniatura de links (estilo pré-visualização WhatsApp).
Instagram: Open Graph + fallback noembed.
"""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlparse

USER_AGENT_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
USER_AGENT_DEFAULT = "Mozilla/5.0 (compatible; MesaBrasileira/1.0)"


def normalizar_url_instagram(url: str) -> str:
    url = (url or "").strip()
    if not url or "instagram.com" not in url:
        return ""
    return url.split("?")[0].rstrip("/") + "/"


def buscar_miniatura(url: str) -> str | None:
    """Devolve URL da imagem de pré-visualização ou None."""
    url = normalizar_url_instagram(url) if "instagram.com" in (url or "") else (url or "").strip()
    if not url:
        return None

    if "instagram.com" in url:
        thumb = _og_image(url, mobile=True)
        if thumb:
            return thumb
        thumb = _noembed(url)
        if thumb:
            return thumb
        return _og_image(url, mobile=False)

    return _og_image(url, mobile=True) or _noembed(url)


def _noembed(url: str) -> str | None:
    api = f"https://noembed.com/embed?format=json&url={quote(url, safe='')}"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": USER_AGENT_DEFAULT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
        return data.get("thumbnail_url") or None
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def _og_image(url: str, *, mobile: bool) -> str | None:
    try:
        headers = {
            "User-Agent": USER_AGENT_MOBILE if mobile else USER_AGENT_DEFAULT,
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'"og:image"\s*:\s*"([^"]+)"',
        r'<meta[^>]+property=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).replace("\\u0026", "&"))
    return None


def _baixar_bytes_imagem(image_url: str) -> tuple[bytes, str] | None:
    """Descarrega bytes de uma URL de imagem (CDN Instagram, etc.)."""
    image_url = (image_url or "").strip()
    if not image_url:
        return None

    header_sets = [
        {
            "User-Agent": USER_AGENT_MOBILE,
            "Referer": "https://www.instagram.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
        {"User-Agent": USER_AGENT_DEFAULT, "Accept": "image/*,*/*;q=0.8"},
    ]
    if "instagram.com" not in image_url and "cdninstagram.com" not in image_url:
        header_sets = list(reversed(header_sets))

    for headers in header_sets:
        try:
            req = urllib.request.Request(image_url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if not data:
                    continue
                content_type = (resp.headers.get("Content-Type") or "").lower()
                return data, content_type
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return None


def baixar_para_imagefield(instance, field_name: str, image_url: str) -> bool:
    """Grava a miniatura no ImageField do modelo (volume MEDIA_ROOT)."""
    from django.core.files.base import ContentFile

    result = _baixar_bytes_imagem(image_url)
    if not result:
        return False
    data, content_type = result

    if "png" in content_type:
        ext = ".png"
    elif "webp" in content_type:
        ext = ".webp"
    else:
        ext = ".jpg"

    path = urlparse(image_url).path
    base = path.split("/")[-1].split(".")[0][:20] if path else "preview"
    filename = f"{base}{ext}"

    field = getattr(instance, field_name)
    if field.name:
        field.delete(save=False)
    field.save(filename, ContentFile(data), save=False)
    return True
