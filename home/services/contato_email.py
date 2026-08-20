"""Envio de mensagens do formulário de contacto."""

from __future__ import annotations

import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from home.models import ConfiguracaoHome
from home.services.email_branding import contexto_email_base

logger = logging.getLogger(__name__)


def _extrair_email(endereco: str) -> str:
    endereco = (endereco or "").strip()
    if not endereco:
        return ""
    match = re.search(r"<([^>]+)>", endereco)
    if match:
        return match.group(1).strip()
    return endereco


def destinatario_contato(config: ConfiguracaoHome | None = None) -> str:
    """
    Email que recebe mensagens do formulário.
    Prioridade: contacto_email na configuração → CONTATO_EMAIL (.env).
    """
    if config is None:
        config = ConfiguracaoHome.get_solo()
    email = (config.contato_email or "").strip()
    if email:
        return email
    return _extrair_email(getattr(settings, "CONTATO_EMAIL", "") or "")


def enviar_mensagem_contato(
    dados: dict, config: ConfiguracaoHome | None = None
) -> tuple[bool, str | None]:
    """
    Envia email para o destino configurado (admin ou CONTATO_EMAIL).
    Retorna (sucesso, mensagem_erro).
    """
    if config is None:
        config = ConfiguracaoHome.get_solo()
    destino = destinatario_contato(config)
    if not destino:
        return False, (
            "Configure o email de contacto em Admin → Configuração da página inicial → Contato "
            "ou a variável CONTATO_EMAIL."
        )

    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not remetente:
        return False, "DEFAULT_FROM_EMAIL não configurado."

    contexto = {
        **contexto_email_base(),
        "nome": dados["nome"],
        "email": dados["email"],
        "assunto": dados["assunto"],
        "mensagem": dados["mensagem"],
        "destino": destino,
    }
    assunto_email = f"[Contato] {dados['assunto']}"
    texto = render_to_string("home/emails/contato_mensagem.txt", contexto)
    html = render_to_string("home/emails/contato_mensagem.html", contexto)

    try:
        msg = EmailMultiAlternatives(
            subject=assunto_email,
            body=texto,
            from_email=remetente,
            to=[destino],
            reply_to=[dados["email"]],
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        logger.info(
            "Contato enviado: de=%s assunto=%r para=%s",
            dados["email"],
            dados["assunto"],
            destino,
        )
        return True, None
    except Exception as exc:
        logger.exception("Falha ao enviar formulário de contacto para %s", destino)
        return False, str(exc)
