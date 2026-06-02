from django.core.management.base import BaseCommand

from home.models import ConfiguracaoHome, VideoEvento


class Command(BaseCommand):
    help = "Busca miniaturas do Instagram para vídeos e configuração da home"

    def handle(self, *args, **options):
        videos_ok = 0
        for video in VideoEvento.objects.exclude(instagram_url=""):
            if video.atualizar_miniatura_instagram():
                video.save(update_fields=["thumbnail", "thumbnail_url"])
                videos_ok += 1
                self.stdout.write(f"  ✓ {video.titulo}")
            else:
                self.stdout.write(self.style.WARNING(f"  ✗ {video.titulo}"))

        config = ConfiguracaoHome.get_solo()
        if config.modo_intro == ConfiguracaoHome.MODO_INSTAGRAM and config.video_instagram_url:
            if config.atualizar_capa_instagram():
                config.save(
                    update_fields=["instagram_imagem", "instagram_imagem_url"]
                )
                self.stdout.write(self.style.SUCCESS("Capa da home atualizada."))
            else:
                self.stdout.write(self.style.WARNING("Capa da home não obtida."))

        self.stdout.write(self.style.SUCCESS(f"Concluído: {videos_ok} vídeo(s) atualizado(s)."))
