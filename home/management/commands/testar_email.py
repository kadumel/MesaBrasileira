from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from home.services.email_branding import contexto_email_base


class Command(BaseCommand):
    help = "Testa o envio de email HTML (logo e cores) com as definições atuais."

    def add_arguments(self, parser):
        parser.add_argument(
            "destino",
            nargs="?",
            default="",
            help="Email de destino (por defeito: EMAIL_HOST_USER)",
        )

    def handle(self, *args, **options):
        destino = (options["destino"] or settings.EMAIL_HOST_USER or "").strip()
        if not destino:
            self.stderr.write(
                "Indique um email: python manage.py testar_email seu@email.com"
            )
            return

        remetente = settings.DEFAULT_FROM_EMAIL
        contexto = {
            **contexto_email_base(),
            "remetente": remetente,
            "smtp_host": settings.EMAIL_HOST,
            "smtp_port": settings.EMAIL_PORT,
        }

        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"From: {remetente}")
        self.stdout.write(f"To: {destino}")
        self.stdout.write(f"Logo: {contexto['logo_url']}")

        assunto = f"Teste de email — {contexto['site_nome']}"
        texto = render_to_string("home/emails/testar_email.txt", contexto)
        html = render_to_string("home/emails/testar_email.html", contexto)

        try:
            send_mail(
                assunto,
                texto,
                remetente,
                [destino],
                html_message=html,
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Falhou: {exc}"))
            return

        if "console" in settings.EMAIL_BACKEND:
            self.stdout.write(
                self.style.WARNING(
                    "Modo consola: o HTML aparece no terminal, não na caixa de entrada."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Email HTML enviado. Se só vir texto simples, abra «Mostrar imagens» "
                    "ou verifique se o cliente está em modo texto."
                )
            )
