"""
Envia emails através de um webhook n8n (HTTPS).

Configure no Railway / .env:
  N8N_WEBHOOK_URL=https://seu-n8n.app/webhook/mesa-brasileira-email
  N8N_WEBHOOK_SECRET=opcional

O workflow n8n recebe JSON e trata do envio (ex.: nó Gmail).
Ver docs/n8n-emails.md
"""

from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)


class N8nWebhookEmailBackend(BaseEmailBackend):
    """Encaminha cada email para um webhook n8n em vez de usar SMTP."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        webhook_url = getattr(settings, "N8N_WEBHOOK_URL", "").strip()
        if not webhook_url:
            if self.fail_silently:
                return 0
            raise ValueError(
                "N8N_WEBHOOK_URL não está definido. "
                "Veja docs/n8n-emails.md"
            )

        sent = 0
        for message in email_messages:
            try:
                self._post_webhook(message, webhook_url)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception("n8n webhook: falha para %s", message.to)
        return sent

    def _post_webhook(self, message: EmailMessage, webhook_url: str) -> None:
        texto = message.body or ""
        html = None
        if isinstance(message, EmailMultiAlternatives):
            for content, mimetype in message.alternatives:
                if mimetype == "text/html":
                    html = content
                    break

        payload = {
            "evento": "email_transacional",
            "de": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "para": list(message.to),
            "assunto": message.subject,
            "texto": texto,
            "html": html or "",
            "cc": list(message.cc) if message.cc else [],
            "bcc": list(message.bcc) if message.bcc else [],
            "reply_to": list(message.reply_to) if message.reply_to else [],
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}

        secret = getattr(settings, "N8N_WEBHOOK_SECRET", "").strip()
        if secret:
            headers["X-Webhook-Secret"] = secret

        request = Request(
            webhook_url,
            data=data,
            headers=headers,
            method="POST",
        )

        timeout = getattr(settings, "EMAIL_TIMEOUT", 30)
        try:
            with urlopen(request, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                if resp.status >= 400:
                    raise OSError(f"n8n webhook HTTP {resp.status}: {body[:500]}")
                logger.info(
                    "n8n webhook OK: assunto=%r para=%s resposta=%s",
                    message.subject,
                    message.to,
                    body[:200],
                )
        except HTTPError as exc:
            err = exc.read().decode("utf-8", errors="replace")
            raise OSError(f"n8n webhook HTTP {exc.code}: {err[:500]}") from exc
        except URLError as exc:
            raise OSError(f"n8n webhook rede: {exc}") from exc
