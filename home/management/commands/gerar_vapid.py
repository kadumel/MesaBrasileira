from django.core.management.base import BaseCommand

from home.models import ConfiguracaoPush
from home.services.pedido_push import gerar_par_vapid, obter_chaves_vapid


class Command(BaseCommand):
    help = "Mostra (ou gera) as chaves VAPID para avisos PWA de pedidos de música."

    def add_arguments(self, parser):
        parser.add_argument(
            "--regenerar",
            action="store_true",
            help="Gera um novo par e guarda na base de dados (invalida subscrições atuais).",
        )

    def handle(self, *args, **options):
        if options["regenerar"]:
            public, private = gerar_par_vapid()
            config = ConfiguracaoPush.get_solo()
            config.vapid_public_key = public
            config.vapid_private_key = private
            config.save(
                update_fields=["vapid_public_key", "vapid_private_key", "atualizado_em"]
            )
            self.stdout.write(self.style.WARNING("Novo par VAPID gerado e guardado."))
        else:
            chaves = obter_chaves_vapid()
            if not chaves:
                self.stderr.write("Não foi possível obter chaves VAPID.")
                return
            public, private = chaves

        self.stdout.write("Adicione ao .env / Railway (opcional — já estão na base de dados):\n")
        self.stdout.write(f"VAPID_PUBLIC_KEY={public}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private}")
        self.stdout.write("VAPID_ADMIN_EMAIL=mailto:contato@mesabrasileira.pt")
