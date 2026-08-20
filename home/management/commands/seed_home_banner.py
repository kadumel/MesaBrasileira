from django.core.management.base import BaseCommand

from home.constants import INSTAGRAM_URL
from home.models import EventoDestaque, Patrocinador, SlideHome

IMG_SAMBA = "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1920&q=80"
IMG_RODA = "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=1920&q=80"
IMG_MUSIC = "https://images.unsplash.com/photo-1511379938549-c1f69419868d?w=1920&q=80"


class Command(BaseCommand):
    help = "Cria slides do carrossel e parceiros de exemplo"

    def handle(self, *args, **options):
        if not SlideHome.objects.exists():
            eventos = list(EventoDestaque.objects.filter(ativo=True).order_by("ordem")[:3])
            slides = []
            for i, evento in enumerate(eventos):
                slides.append(
                    SlideHome(
                        titulo=evento.titulo,
                        subtitulo=evento.local or "Projeto Mesa Brasileira",
                        imagem_url=evento.imagem_exibir or IMG_SAMBA,
                        tipo=SlideHome.TIPO_EVENTO,
                        evento=evento,
                        ordem=i + 1,
                    )
                )
            slides.append(
                SlideHome(
                    titulo="Siga a nossa roda",
                    subtitulo="@mesabrasileirapt no Instagram",
                    imagem_url=IMG_MUSIC,
                    tipo=SlideHome.TIPO_PROPAGANDA,
                    link=INSTAGRAM_URL,
                    ordem=10,
                )
            )
            SlideHome.objects.bulk_create(slides)
            self.stdout.write(self.style.SUCCESS(f"{len(slides)} slides criados."))
        else:
            self.stdout.write("Slides já existem — ignorado.")

        if not Patrocinador.objects.exists():
            Patrocinador.objects.bulk_create(
                [
                    Patrocinador(
                        nome="Parceiro Cultural",
                        logo_url="https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=400&q=80",
                        site=INSTAGRAM_URL,
                        ordem=1,
                    ),
                    Patrocinador(
                        nome="Apoio Local",
                        logo_url="https://images.unsplash.com/photo-1556761175-b413da4baf72?w=400&q=80",
                        site="",
                        ordem=2,
                    ),
                    Patrocinador(
                        nome="Mecenas Samba",
                        logo_url="https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&q=80",
                        site=INSTAGRAM_URL,
                        ordem=3,
                    ),
                ]
            )
            self.stdout.write(self.style.SUCCESS("Parceiros de exemplo criados."))
        else:
            self.stdout.write("Parceiros já existem — ignorado.")
