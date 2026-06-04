from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .constants import INSTAGRAM_URL
from .cart import cart_count
from .forms import (
    AdicionarCarrinhoForm,
    MarcarPedidoTocadoForm,
    PedidoMusicaForm,
    RejeitarPedidoMusicaForm,
)
from .models import (
    ConfiguracaoHome,
    EventoDestaque,
    EventoSamba,
    Patrocinador,
    PedidoMusica,
    Produto,
    SlideHome,
    VideoEvento,
)

EQUIPE_GROUP_NAME = getattr(settings, "MESA_BRASILEIRA_EQUIPE_GROUP_NAME", "Equipe")


def user_pode_marcar(user):
    """Utilizadores com sessão iniciada gerem a fila na página de pedidos."""
    return user.is_authenticated


def _pedido_fila_json(pedido: PedidoMusica) -> dict:
    """Payload JSON da fila (ordem e refresh automático)."""
    return {
        "id": pedido.pk,
        "musica": pedido.musica,
        "artista": pedido.artista,
        "pedido_por": pedido.pedido_por,
        "mensagem": pedido.mensagem,
        "observacao_equipe": pedido.observacao_equipe,
        "marcado_por_exibir": pedido.marcado_por_exibir,
        "tocado": pedido.tocado,
        "rejeitado": pedido.rejeitado,
        "criado_em": pedido.criado_em.isoformat(),
        "tocado_em": pedido.tocado_em.isoformat() if pedido.tocado_em else None,
        "rejeitado_em": pedido.rejeitado_em.isoformat() if pedido.rejeitado_em else None,
        "atualizado_em": pedido.atualizado_em.isoformat(),
    }


def _contagem_em_fila(evento_samba):
    if not evento_samba:
        return 0
    return evento_samba.pedidos.filter(tocado=False, rejeitado=False).count()


def _fila_limite_context(evento_samba):
    config = ConfiguracaoHome.get_solo()
    limite = config.limite_pedidos_em_fila
    total_em_fila = _contagem_em_fila(evento_samba)
    return {
        "config_home": config,
        "limite_pedidos_em_fila": limite,
        "total_em_fila": total_em_fila,
        "fila_cheia": bool(evento_samba and total_em_fila >= limite),
    }


def _evento_pedidos_context():
    evento_samba = (
        EventoSamba.objects.filter(ativo=True, aceita_pedidos=True)
        .order_by("-data")
        .first()
    )
    pedidos = []
    form = None
    if evento_samba:
        pedidos = PedidoMusica.ordenar_para_fila(
            evento_samba.pedidos.select_related("marcado_por")
        )[:50]
        form = PedidoMusicaForm()
    return {
        "evento_samba": evento_samba,
        "pedidos": pedidos,
        "form_pedido": form,
        **_fila_limite_context(evento_samba),
    }


def index(request):
    produtos_qs = Produto.objects.filter(ativo=True)
    context = {
        "config_home": ConfiguracaoHome.get_solo(),
        "slides_home": SlideHome.objects.filter(ativo=True).select_related("evento"),
        "patrocinadores": Patrocinador.objects.filter(ativo=True),
        "eventos_destaque": EventoDestaque.objects.filter(ativo=True, destaque=True)[:6],
        "produtos": produtos_qs[:6],
        "total_produtos": produtos_qs.count(),
        "videos": VideoEvento.objects.filter(ativo=True, destaque=True).select_related(
            "evento"
        ),
        "nav_active": "home",
    }
    return render(request, "home/index.html", context)


def pedir_musica(request):
    context = {
        **_evento_pedidos_context(),
        "pode_marcar": user_pode_marcar(request.user),
        "nav_active": "pedidos",
    }
    return render(request, "home/pedir_musica.html", context)


def eventos(request):
    context = {
        "eventos": EventoDestaque.objects.filter(ativo=True),
        "eventos_samba": EventoSamba.objects.filter(ativo=True),
        "nav_active": "eventos",
    }
    return render(request, "home/eventos.html", context)


def evento_detail(request, pk):
    evento = get_object_or_404(EventoDestaque, pk=pk, ativo=True)
    context = {
        "evento": evento,
        "nav_active": "eventos",
    }
    return render(request, "home/evento_detail.html", context)


def _eventos_com_videos_queryset():
    return (
        EventoSamba.objects.filter(videos__ativo=True)
        .annotate(
            qtd_videos=Count("videos", filter=Q(videos__ativo=True), distinct=True)
        )
        .filter(qtd_videos__gt=0)
        .distinct()
        .order_by("-data")
    )


def videos(request, evento_pk=None):
    eventos_com_videos = list(_eventos_com_videos_queryset())
    evento_selecionado = None
    videos_lista = VideoEvento.objects.none()
    videos_sem_evento = VideoEvento.objects.filter(
        evento__isnull=True, ativo=True
    ).order_by("ordem", "-criado_em")

    if evento_pk is not None:
        evento_selecionado = get_object_or_404(EventoSamba, pk=evento_pk)
        videos_lista = (
            VideoEvento.objects.filter(evento=evento_selecionado, ativo=True)
            .select_related("evento")
            .order_by("ordem", "-criado_em")
        )
    elif eventos_com_videos:
        evento_selecionado = eventos_com_videos[0]
        videos_lista = (
            VideoEvento.objects.filter(evento=evento_selecionado, ativo=True)
            .select_related("evento")
            .order_by("ordem", "-criado_em")
        )

    context = {
        "config_home": ConfiguracaoHome.get_solo(),
        "eventos_com_videos": eventos_com_videos,
        "evento_selecionado": evento_selecionado,
        "videos": videos_lista,
        "videos_sem_evento": videos_sem_evento,
        "tem_videos": videos_lista.exists() or videos_sem_evento.exists(),
        "nav_active": "videos",
    }
    return render(request, "home/videos.html", context)


def loja(request):
    context = {
        "produtos": Produto.objects.filter(ativo=True).prefetch_related("tamanhos"),
        "nav_active": "loja",
        "cart_count": cart_count(request.session),
    }
    return render(request, "home/loja.html", context)


def produto_detail(request, pk):
    produto = get_object_or_404(
        Produto.objects.prefetch_related("tamanhos"),
        pk=pk,
        ativo=True,
    )
    context = {
        "produto": produto,
        "nav_active": "loja",
        "cart_count": cart_count(request.session),
        "form_carrinho": AdicionarCarrinhoForm(produto=produto),
    }
    return render(request, "home/produto_detail.html", context)


@require_POST
def pedido_musica(request):
    evento_id = request.POST.get("evento_id")
    evento = get_object_or_404(
        EventoSamba,
        pk=evento_id,
        ativo=True,
        aceita_pedidos=True,
    )
    config = ConfiguracaoHome.get_solo()
    em_fila = _contagem_em_fila(evento)
    if em_fila >= config.limite_pedidos_em_fila:
        msg = (
            f"A fila está cheia ({em_fila}/{config.limite_pedidos_em_fila} em espera). "
            "Aguarde a roda tocar mais músicas antes de pedir outra."
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": False,
                    "fila_cheia": True,
                    "error": msg,
                    "total_em_fila": em_fila,
                    "limite_em_fila": config.limite_pedidos_em_fila,
                },
                status=403,
            )
        return HttpResponseRedirect(reverse("home:pedir_musica"))

    form = PedidoMusicaForm(request.POST)
    if form.is_valid():
        pedido = form.save(commit=False)
        pedido.evento = evento
        pedido.save()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": True,
                    "pedido": _pedido_fila_json(pedido),
                }
            )
        return HttpResponseRedirect(reverse("home:pedir_musica"))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return HttpResponseRedirect(reverse("home:pedir_musica"))


@require_POST
@login_required
def marcar_pedido_tocado(request, pk):
    if not user_pode_marcar(request.user):
        raise PermissionDenied
    pedido = get_object_or_404(PedidoMusica, pk=pk)
    if not pedido.em_fila:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": False, "error": "Este pedido já foi tratado."},
                status=400,
            )
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    form = MarcarPedidoTocadoForm(request.POST)
    if not form.is_valid():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    pedido.marcar_tocado(
        form.cleaned_data.get("observacao_equipe", ""),
        user=request.user,
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        pedido.refresh_from_db()
        return JsonResponse(
            {
                "ok": True,
                "pedido": _pedido_fila_json(pedido),
            }
        )
    return HttpResponseRedirect(reverse("home:pedir_musica"))


@require_POST
@login_required
def marcar_pedido_rejeitado(request, pk):
    if not user_pode_marcar(request.user):
        raise PermissionDenied
    pedido = get_object_or_404(PedidoMusica, pk=pk)
    if not pedido.em_fila:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": False, "error": "Este pedido já foi tratado."},
                status=400,
            )
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    form = RejeitarPedidoMusicaForm(request.POST)
    if not form.is_valid():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    try:
        pedido.marcar_rejeitado(
            form.cleaned_data["observacao_equipe"],
            user=request.user,
        )
    except ValueError as exc:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": False, "errors": {"observacao_equipe": [str(exc)]}},
                status=400,
            )
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        pedido.refresh_from_db()
        return JsonResponse(
            {
                "ok": True,
                "pedido": _pedido_fila_json(pedido),
            }
        )
    return HttpResponseRedirect(reverse("home:pedir_musica"))


@require_GET
def fila_pedidos_json(request, evento_id):
    evento = get_object_or_404(EventoSamba, pk=evento_id, ativo=True)
    config = ConfiguracaoHome.get_solo()
    limite = config.limite_pedidos_em_fila
    total_em_fila = _contagem_em_fila(evento)
    pedidos = PedidoMusica.ordenar_para_fila(
        evento.pedidos.select_related("marcado_por")
    )[:50]
    data = [_pedido_fila_json(p) for p in pedidos]
    response = JsonResponse(
        {
            "pedidos": data,
            "pode_marcar": user_pode_marcar(request.user),
            "limite_em_fila": limite,
            "total_em_fila": total_em_fila,
            "fila_cheia": total_em_fila >= limite,
        }
    )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response
