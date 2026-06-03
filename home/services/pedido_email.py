import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from home.models import Pedido
from home.services.email_branding import contexto_email_base

logger = logging.getLogger(__name__)


def _enviar_email_pedido(
    pedido: Pedido,
    assunto: str,
    template_base: str,
    contexto_extra: dict | None = None,
) -> tuple[bool, str | None]:
    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not remetente:
        return False, "DEFAULT_FROM_EMAIL não configurado."

    contexto = {
        **contexto_email_base(),
        "pedido": pedido,
        **(contexto_extra or {}),
    }
    mensagem_texto = render_to_string(f"home/emails/{template_base}.txt", contexto)
    mensagem_html = render_to_string(f"home/emails/{template_base}.html", contexto)

    try:
        send_mail(
            assunto,
            mensagem_texto,
            remetente,
            [pedido.email],
            html_message=mensagem_html,
            fail_silently=False,
        )
        return True, None
    except Exception as exc:
        logger.exception(
            "Falha ao enviar email (%s) pedido %s para %s: %s",
            template_base,
            pedido.numero,
            pedido.email,
            exc,
        )
        return False, str(exc)


def enviar_email_confirmacao(pedido: Pedido) -> tuple[bool, str | None]:
    """
    Envia email de confirmação. Retorna (sucesso, mensagem_erro).
    """
    if "console" in settings.EMAIL_BACKEND:
        logger.warning(
            "EMAIL_BACKEND é consola — o email não chega à caixa de entrada."
        )
    elif "n8n" in settings.EMAIL_BACKEND:
        logger.info(
            "Email via n8n webhook: %s",
            getattr(settings, "N8N_WEBHOOK_URL", ""),
        )

    assunto = f"Confirme o seu pedido {pedido.numero} — Mesa Brasileira"
    ok, erro = _enviar_email_pedido(
        pedido,
        assunto,
        "confirmar_pedido",
        {"url_confirmacao": pedido.url_confirmacao_email()},
    )
    if ok:
        logger.info("Email de confirmação enviado: pedido=%s", pedido.numero)
    return ok, erro


def enviar_email_pagamento_confirmado(pedido: Pedido) -> tuple[bool, str | None]:
    assunto = f"Pagamento recebido — pedido {pedido.numero} | Mesa Brasileira"
    ok, erro = _enviar_email_pedido(pedido, assunto, "pagamento_confirmado")
    if ok:
        logger.info("Email pagamento confirmado: pedido=%s", pedido.numero)
    return ok, erro
