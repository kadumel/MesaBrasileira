import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from home.models import Pedido

logger = logging.getLogger(__name__)


def enviar_email_confirmacao(pedido: Pedido) -> tuple[bool, str | None]:
    """
    Envia email de confirmação. Retorna (sucesso, mensagem_erro).
    """
    assunto = f"Confirme o seu pedido {pedido.numero} — Mesa Brasileira"
    contexto = {
        "pedido": pedido,
        "url_confirmacao": pedido.url_confirmacao_email(),
        "site_nome": "Mesa Brasileira",
    }
    mensagem_texto = render_to_string("home/emails/confirmar_pedido.txt", contexto)
    mensagem_html = render_to_string("home/emails/confirmar_pedido.html", contexto)
    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not remetente:
        return False, "DEFAULT_FROM_EMAIL não configurado."

    if "console" in settings.EMAIL_BACKEND:
        logger.warning(
            "EMAIL_BACKEND é consola — o email não chega à caixa de entrada. "
            "Configure EMAIL_HOST_USER no .env e reinicie o servidor."
        )

    try:
        send_mail(
            assunto,
            mensagem_texto,
            remetente,
            [pedido.email],
            html_message=mensagem_html,
            fail_silently=False,
        )
        logger.info(
            "Email de confirmação enviado: pedido=%s para=%s backend=%s",
            pedido.numero,
            pedido.email,
            settings.EMAIL_BACKEND,
        )
        return True, None
    except Exception as exc:
        logger.exception(
            "Falha ao enviar email do pedido %s para %s: %s",
            pedido.numero,
            pedido.email,
            exc,
        )
        return False, str(exc)
