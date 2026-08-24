import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from home.models import CadastroEmailToken
from home.services.email_branding import contexto_email_base

logger = logging.getLogger(__name__)


def enviar_email_confirmacao_cadastro(user) -> tuple[bool, str | None]:
    """Envia o email com o link de validação da conta. Retorna (ok, erro)."""
    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not remetente:
        return False, "DEFAULT_FROM_EMAIL não configurado."

    token = getattr(user, "token_cadastro", None)
    if token is None:
        token = CadastroEmailToken.renovar_para(user)

    contexto = {
        **contexto_email_base(),
        "user": user,
        "nome": (user.get_full_name() or user.get_username()).strip(),
        "url_confirmacao": token.url_confirmacao(),
        "horas_validade": int(getattr(settings, "CADASTRO_TOKEN_EMAIL_HORAS", 48)),
    }
    mensagem_texto = render_to_string("home/emails/confirmar_cadastro.txt", contexto)
    mensagem_html = render_to_string("home/emails/confirmar_cadastro.html", contexto)
    assunto = "Confirme o seu cadastro — Mesa Brasileira"

    try:
        send_mail(
            assunto,
            mensagem_texto,
            remetente,
            [user.email],
            html_message=mensagem_html,
            fail_silently=False,
        )
        logger.info("Email de confirmação de cadastro enviado: user=%s", user.pk)
        return True, None
    except Exception as exc:
        logger.exception(
            "Falha ao enviar confirmação de cadastro para %s: %s",
            user.email,
            exc,
        )
        return False, str(exc)
