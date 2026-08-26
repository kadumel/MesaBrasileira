"""Caricaturas da roda — cinco sorteadas a cada visita à home."""

import random

from django.templatetags.static import static
from django.urls import reverse


def _artista(src, caption, alt=None, extra_class="", cache="1"):
    return {
        "src": src,
        "caption": caption,
        "alt": alt or f"Caricatura de {caption}",
        "extra_class": extra_class,
        "cache": cache,
    }


RODA_SAMBISTA_POOL = (
    _artista("home/img/roda/arlindo-cruz.jpg", "Arlindo Cruz"),
    _artista(
        "home/img/roda/sombrinha.jpg",
        "Fundo de Quintal",
        alt="Caricatura do Fundo de Quintal",
        extra_class="roda-item--grupo",
        cache="6",
    ),
    _artista("home/img/roda/beth-carvalho.jpg", "Beth Carvalho"),
    _artista(
        "home/img/roda/dona-ivone-lara.jpg",
        "Ivone Lara",
        alt="Caricatura de Dona Ivone Lara",
        extra_class="roda-item--retrato",
        cache="1",
    ),
    _artista("home/img/roda/zeca-pagodinho.jpg", "Zeca Pagodinho", cache="2"),
    _artista("home/img/roda/xande-de-pilar.jpg", "Xande de Pilares"),
    _artista("home/img/roda/cartola.jpg", "Cartola"),
    _artista("home/img/roda/martinho-da-vila.jpg", "Martinho da Vila"),
    _artista("home/img/roda/paulinho-da-viola.jpg", "Paulinho da Viola"),
    _artista("home/img/roda/clara-nunes.jpg", "Clara Nunes"),
    _artista("home/img/roda/jorge-aragao.jpg", "Jorge Aragão"),
    _artista("home/img/roda/almir-guineto.jpg", "Almir Guineto"),
    _artista("home/img/roda/bezerra-da-silva.jpg", "Bezerra da Silva"),
    _artista("home/img/roda/joao-nogueira.jpg", "João Nogueira"),
    _artista("home/img/roda/nelson-cavaquinho.jpg", "Nelson Cavaquinho"),
    _artista("home/img/roda/adoniran-barbosa.jpg", "Adoniran Barbosa"),
    _artista("home/img/roda/noel-rosa.jpg", "Noel Rosa"),
    _artista("home/img/roda/candeia.jpg", "Candeia"),
    _artista("home/img/roda/benito-di-paula.jpg", "Benito di Paula"),
    _artista(
        "home/img/roda/jovelina-perola-negra.jpg",
        "Jovelina",
        alt="Caricatura de Jovelina Pérola Negra",
    ),
)

RODA_SAMBISTA_SLOTS = (
    {
        "url_name": "home:pedir_musica",
        "page_name": "Pedir música",
        "order": "2",
        "depth": "0.28",
        "x": "75%",
        "y": "22%",
        "s": "0.88",
        "rot": "8deg",
        "z": "3",
        "w": "6.4rem",
    },
    {
        "url_name": "home:eventos",
        "page_name": "Eventos",
        "order": "4",
        "depth": "0.42",
        "x": "90%",
        "y": "62%",
        "s": "1.0",
        "rot": "6deg",
        "z": "5",
        "w": "6.6rem",
    },
    {
        "url_name": "home:sobre",
        "page_name": "Sobre",
        "order": "8",
        "depth": "0.55",
        "x": "50%",
        "y": "86%",
        "s": "1.12",
        "rot": "0deg",
        "z": "7",
        "w": "7rem",
    },
    {
        "url_name": "home:contato",
        "page_name": "Contato",
        "order": "6",
        "depth": "0.42",
        "x": "10%",
        "y": "62%",
        "s": "1.0",
        "rot": "-8deg",
        "z": "5",
        "w": "6.6rem",
    },
    {
        "href": "#parceiros",
        "page_name": "Parceiros",
        "order": "10",
        "depth": "0.28",
        "x": "25%",
        "y": "22%",
        "s": "0.88",
        "rot": "-8deg",
        "z": "3",
        "w": "6.4rem",
    },
)


def escolher_sambistas_roda(k=5):
    artistas = random.sample(RODA_SAMBISTA_POOL, k=min(k, len(RODA_SAMBISTA_POOL)))
    escolhidos = []
    for slot, artista in zip(RODA_SAMBISTA_SLOTS, artistas):
        item = {**slot, **artista}
        url_name = item.pop("url_name", None)
        if url_name:
            item["href"] = reverse(url_name)
        escolhidos.append(item)
    return escolhidos


def pool_for_frontend():
    pool = []
    for artista in RODA_SAMBISTA_POOL:
        src = static(artista["src"])
        cache = artista.get("cache")
        if cache:
            src = f"{src}?v={cache}"
        pool.append(
            {
                "src": src,
                "caption": artista["caption"],
                "alt": artista["alt"],
                "extraClass": artista["extra_class"],
            }
        )
    return pool
