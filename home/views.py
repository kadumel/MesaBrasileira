from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .constants import INSTAGRAM_URL
from .forms import MarcarPedidoTocadoForm, PedidoMusicaForm
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


def _evento_pedidos_context():
    evento_samba = (
        EventoSamba.objects.filter(ativo=True, aceita_pedidos=True)
        .order_by("-data")
        .first()
    )
    pedidos = []
    form = None
    if evento_samba:
        pedidos = evento_samba.pedidos.all().order_by("tocado", "id")[:50]
        form = PedidoMusicaForm()
    return {
        "evento_samba": evento_samba,
        "pedidos": pedidos,
        "form_pedido": form,
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
        "videos": VideoEvento.objects.filter(ativo=True).select_related("evento"),
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


def loja(request):
    context = {
        "produtos": Produto.objects.filter(ativo=True),
        "nav_active": "loja",
    }
    return render(request, "home/loja.html", context)


def produto_detail(request, pk):
    produto = get_object_or_404(Produto, pk=pk, ativo=True)
    context = {
        "produto": produto,
        "nav_active": "loja",
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
    form = PedidoMusicaForm(request.POST)
    if form.is_valid():
        pedido = form.save(commit=False)
        pedido.evento = evento
        pedido.save()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": True,
                    "pedido": {
                        "id": pedido.pk,
                        "musica": pedido.musica,
                        "artista": pedido.artista,
                        "pedido_por": pedido.pedido_por,
                        "tocado": pedido.tocado,
                    },
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
    form = MarcarPedidoTocadoForm(request.POST)
    if not form.is_valid():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return HttpResponseRedirect(reverse("home:pedir_musica"))
    pedido.marcar_tocado(form.cleaned_data.get("observacao_equipe", ""))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "pedido": {
                    "id": pedido.pk,
                    "musica": pedido.musica,
                    "artista": pedido.artista,
                    "pedido_por": pedido.pedido_por,
                    "mensagem": pedido.mensagem,
                    "observacao_equipe": pedido.observacao_equipe,
                    "tocado": True,
                },
            }
        )
    return HttpResponseRedirect(reverse("home:pedir_musica"))


@require_GET
def fila_pedidos_json(request, evento_id):
    evento = get_object_or_404(EventoSamba, pk=evento_id, ativo=True)
    pedidos = evento.pedidos.all().order_by("tocado", "id")[:50]
    data = [
        {
            "id": p.pk,
            "musica": p.musica,
            "artista": p.artista,
            "pedido_por": p.pedido_por,
            "mensagem": p.mensagem,
            "observacao_equipe": p.observacao_equipe,
            "tocado": p.tocado,
            "criado_em": p.criado_em.isoformat(),
        }
        for p in pedidos
    ]
    response = JsonResponse(
        {
            "pedidos": data,
            "pode_marcar": user_pode_marcar(request.user),
        }
    )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response
