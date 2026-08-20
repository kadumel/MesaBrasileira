"""Avisos Web Push quando entra um pedido de música na fila."""

from __future__ import annotations

import base64
import json
import logging

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def gerar_par_vapid() -> tuple[str, str]:
    """Devolve (chave pública base64url, chave privada raw base64url)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    raw_priv = private_key.private_numbers().private_value.to_bytes(32, "big")
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return _b64url(public_raw), _b64url(raw_priv)


def _instancia_vapid(private_key: str):
    from py_vapid import Vapid

    private_key = (private_key or "").strip()
    if "-----BEGIN" in private_key:
        return Vapid.from_pem(private_key.encode("utf-8"))
    return Vapid.from_string(private_key)


def obter_chaves_vapid() -> tuple[str, str] | None:
    """
    Chaves VAPID: variáveis de ambiente têm prioridade;
    senão usa (e gera) o par guardado na base de dados.
    """
    public = (getattr(settings, "VAPID_PUBLIC_KEY", "") or "").strip()
    private = (getattr(settings, "VAPID_PRIVATE_KEY", "") or "").strip()
    if public and private:
        return public, private.replace("\\n", "\n")

    from home.models import ConfiguracaoPush

    config = ConfiguracaoPush.get_solo()
    if config.vapid_public_key and config.vapid_private_key:
        return config.vapid_public_key, config.vapid_private_key

    try:
        public, private = gerar_par_vapid()
    except Exception:
        logger.exception("Não foi possível gerar chaves VAPID.")
        return None

    config.vapid_public_key = public
    config.vapid_private_key = private
    config.save(update_fields=["vapid_public_key", "vapid_private_key", "atualizado_em"])
    logger.info("Chaves VAPID geradas e guardadas para notificações PWA.")
    return public, private


def vapid_public_key() -> str:
    chaves = obter_chaves_vapid()
    return chaves[0] if chaves else ""


def _corpo_pedido(musica: str, artista: str) -> str:
    musica = (musica or "").strip()
    artista = (artista or "").strip()
    if musica and artista:
        return f"{musica} — {artista}"
    return musica or artista or "Novo pedido na fila"


def _vapid_claims() -> dict:
    email = (
        (getattr(settings, "VAPID_ADMIN_EMAIL", "") or "").strip()
        or (getattr(settings, "CONTATO_EMAIL", "") or "").strip()
        or (getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()
    )
    if email and not email.startswith("mailto:") and not email.startswith("https:"):
        if "<" in email and ">" in email:
            email = email[email.find("<") + 1 : email.find(">")].strip()
        email = f"mailto:{email}"
    if not email:
        email = "mailto:noreply@mesabrasileira.pt"
    return {"sub": email}


def notificar_novo_pedido(*, musica: str, artista: str, pedido_id: int | None = None) -> int:
    """
    Envia um aviso a todos os aparelhos da equipa inscritos.
    Devolve o número de envios bem sucedidos. Falhas não rebentam o pedido.
    """
    chaves = obter_chaves_vapid()
    if not chaves:
        return 0

    from home.models import InscricaoPush

    inscricoes = list(
        InscricaoPush.objects.values("id", "endpoint", "p256dh", "auth")
    )
    if not inscricoes:
        return 0

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush não está instalado — avisos PWA desligados.")
        return 0

    try:
        vapid = _instancia_vapid(chaves[1])
    except Exception:
        logger.exception("Chave VAPID inválida — avisos PWA desligados.")
        return 0

    url_fila = reverse("home:pedir_musica")
    payload = json.dumps(
        {
            "title": "Pedido de música",
            "body": _corpo_pedido(musica, artista),
            "url": url_fila,
            "tag": f"pedido-musica-{pedido_id}" if pedido_id else "pedido-musica",
        },
        ensure_ascii=False,
    )
    sub = _vapid_claims()["sub"]
    enviados = 0

    for item in inscricoes:
        try:
            webpush(
                subscription_info={
                    "endpoint": item["endpoint"],
                    "keys": {
                        "p256dh": item["p256dh"],
                        "auth": item["auth"],
                    },
                },
                data=payload,
                vapid_private_key=vapid,
                vapid_claims={"sub": sub},
                ttl=300,
            )
            enviados += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                InscricaoPush.objects.filter(pk=item["id"]).delete()
                logger.info("Inscrição Push expirada removida: %s", item["endpoint"][:64])
            else:
                logger.warning(
                    "Falha ao enviar Push (pedido=%s, status=%s): %s",
                    pedido_id,
                    status,
                    exc,
                )
        except Exception:
            logger.exception(
                "Erro inesperado no Push (pedido=%s, inscrição=%s)",
                pedido_id,
                item["id"],
            )

    return enviados
