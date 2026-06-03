from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from home.constants import INSTAGRAM_URL as INSTAGRAM
from home.models import (
    EventoDestaque,
    EventoSamba,
    Patrocinador,
    Produto,
    SlideHome,
    TamanhoProduto,
    VideoEvento,
)

# Imagens temáticas (samba / cultura brasileira) — substitua por URLs do Instagram no admin
IMG_SAMBA = "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1200&q=80"
IMG_RODA = "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=1200&q=80"
IMG_MUSIC = "https://images.unsplash.com/photo-1511379938549-c1f69419868d?w=1200&q=80"
IMG_CROWD = "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=1200&q=80"
IMG_SHIRT = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80"
IMG_CAP = "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&q=80"
IMG_BAG = "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80"


class Command(BaseCommand):
    help = "Carrega dados de demonstração do Projeto Mesa Brasileira"

    def handle(self, *args, **options):
        if EventoDestaque.objects.exists():
            self.stdout.write(self.style.WARNING("Dados já existem — a ignorar seed."))
            return

        agora = timezone.now()

        eventos = [
            EventoDestaque(
                titulo="Roda Mesa Brasileira",
                descricao=(
                    "Encontro mensal de samba com mesa aberta à comunidade. "
                    "Traga a sua energia e peça a sua música."
                ),
                imagem_url=IMG_SAMBA,
                data_evento=(agora + timedelta(days=14)).date(),
                local="Lisboa",
                link=INSTAGRAM,
                ordem=1,
                destaque=True,
            ),
            EventoDestaque(
                titulo="Samba na Praça",
                descricao="Roda ao ar livre com convidados especiais e muita partilha.",
                imagem_url=IMG_RODA,
                data_evento=(agora + timedelta(days=35)).date(),
                local="Porto",
                link=INSTAGRAM,
                ordem=2,
                destaque=True,
            ),
            EventoDestaque(
                titulo="Noite de Partido Alto",
                descricao="Clássicos do samba e sambas-enredo para cantar em coro.",
                imagem_url=IMG_MUSIC,
                data_evento=(agora + timedelta(days=52)).date(),
                local="Coimbra",
                link=INSTAGRAM,
                ordem=3,
                destaque=False,
            ),
        ]
        EventoDestaque.objects.bulk_create(eventos)

        for i, evento in enumerate(EventoDestaque.objects.order_by("ordem")):
            SlideHome.objects.create(
                titulo=evento.titulo,
                subtitulo=evento.local or "Em respeito ao nosso samba",
                imagem_url=evento.imagem_url,
                tipo=SlideHome.TIPO_EVENTO,
                evento=evento,
                ordem=i + 1,
            )
        SlideHome.objects.create(
            titulo="Conheça o projeto",
            subtitulo="Samba, mesa e comunidade",
            imagem_url=IMG_MUSIC,
            tipo=SlideHome.TIPO_PROPAGANDA,
            link=INSTAGRAM,
            ordem=10,
        )

        Patrocinador.objects.bulk_create(
            [
                Patrocinador(
                    nome="Parceiro Cultural",
                    logo_url="https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=400&q=80",
                    site=INSTAGRAM,
                    ordem=1,
                ),
                Patrocinador(
                    nome="Apoio à Roda",
                    logo_url="https://images.unsplash.com/photo-1556761175-b413da4baf72?w=400&q=80",
                    ordem=2,
                ),
            ]
        )

        produtos = [
            Produto(
                nome="T-shirt Mesa Brasileira",
                descricao="Algodão premium com estampa exclusiva do projeto.",
                preco=Decimal("22.00"),
                imagem_url=IMG_SHIRT,
                requer_tamanho=True,
                destaque=True,
                ordem=1,
            ),
            Produto(
                nome="Boné MB",
                descricao="Boné ajustável com logo bordado.",
                preco=Decimal("15.00"),
                imagem_url=IMG_CAP,
                link_compra=INSTAGRAM,
                ordem=2,
            ),
            Produto(
                nome="Saco de pano",
                descricao="Saco reutilizável para levar a energia da roda.",
                preco=Decimal("12.00"),
                imagem_url=IMG_BAG,
                link_compra=INSTAGRAM,
                ordem=3,
            ),
        ]
        Produto.objects.bulk_create(produtos)
        camisola = Produto.objects.filter(nome="T-shirt Mesa Brasileira").first()
        if camisola:
            TamanhoProduto.objects.bulk_create(
                [
                    TamanhoProduto(produto=camisola, codigo=codigo)
                    for codigo, _ in TamanhoProduto.TAMANHOS
                ]
            )

        evento_samba = EventoSamba.objects.create(
            titulo="Roda Mesa Brasileira — Ao vivo",
            descricao=(
                "Evento ativo para pedidos de música. A mesa toca por ordem "
                "e marca cada pedido quando a música soa."
            ),
            data=agora - timedelta(hours=1),
            local="Lisboa",
            imagem_url=IMG_CROWD,
            aceita_pedidos=True,
            ativo=True,
        )

        VideoEvento.objects.bulk_create(
            [
                VideoEvento(
                    titulo="Momentos da roda",
                    evento=evento_samba,
                    instagram_url=INSTAGRAM,
                    thumbnail_url=IMG_SAMBA,
                    ordem=1,
                ),
                VideoEvento(
                    titulo="Samba e comunidade",
                    evento=evento_samba,
                    instagram_url=INSTAGRAM,
                    thumbnail_url=IMG_RODA,
                    ordem=2,
                ),
                VideoEvento(
                    titulo="Bastidores do projeto",
                    instagram_url=INSTAGRAM,
                    thumbnail_url=IMG_MUSIC,
                    ordem=3,
                ),
            ]
        )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados com sucesso."))
