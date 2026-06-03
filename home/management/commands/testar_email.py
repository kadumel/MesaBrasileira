from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Testa o envio de email com as definições atuais (SMTP / consola)."

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

        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To: {destino}")

        try:
            send_mail(
                "Teste Mesa Brasileira",
                "Se recebeu este email, o SMTP está a funcionar.",
                settings.DEFAULT_FROM_EMAIL,
                [destino],
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Falhou: {exc}"))
            return

        if "console" in settings.EMAIL_BACKEND:
            self.stdout.write(
                self.style.WARNING(
                    "Modo consola: o texto apareceu no terminal, não na caixa de entrada."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Email enviado com sucesso."))
