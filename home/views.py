import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET, require_POST

from .constants import INSTAGRAM_URL
from .cart import cart_count
from .forms import (
    AdicionarCarrinhoForm,
    ContatoForm,
    MarcarPedidoTocadoForm,
    PedidoMusicaForm,
    RejeitarPedidoMusicaForm,
)
from .models import (
    URL_MAX_LENGTH,
    ConfiguracaoHome,
    Contato,
    EventoDestaque,
    EventoSamba,
    InscricaoPush,
    MotivoRejeicao,
    Patrocinador,
    PedidoMusica,
    Produto,
    SlideHome,
    SobrePagina,
    VideoEvento,
)
from .services.contato_email import enviar_mensagem_contato
from .services.pedido_push import notificar_novo_pedido, vapid_public_key

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
        "motivo_rejeicao": pedido.motivo_rejeicao_id,
        "motivo_rejeicao_exibir": pedido.motivo_rejeicao_exibir,
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
            evento_samba.pedidos.select_related("marcado_por", "motivo_rejeicao")
        )[:50]
        form = PedidoMusicaForm()
    return {
        "evento_samba": evento_samba,
        "pedidos": pedidos,
        "form_pedido": form,
        "motivos_rejeicao": MotivoRejeicao.objects.filter(ativo=True),
        **_fila_limite_context(evento_samba),
    }


def index(request):
    produtos_qs = Produto.objects.filter(ativo=True)
    context = {
        "config_home": ConfiguracaoHome.get_solo(),
        "slides_home": SlideHome.objects.filter(ativo=True).select_related("evento"),
        "parceiros": Patrocinador.objects.filter(ativo=True),
        "eventos_destaque": EventoDestaque.objects.filter(ativo=True, destaque=True)[:6],
        "produtos": produtos_qs[:6],
        "total_produtos": produtos_qs.count(),
        "nav_active": "home",
    }
    return render(request, "home/index.html", context)


@require_GET
@cache_control(max_age=86400, public=True)
def web_manifest(request):
    """Manifest PWA — nome MB.pt."""
    from django.contrib.staticfiles.finders import find

    path = find("home/manifest.webmanifest")
    if not path:
        return HttpResponse(status=404)
    return FileResponse(
        open(path, "rb"),
        content_type="application/manifest+json",
    )


@require_GET
@cache_control(no_cache=True, must_revalidate=True)
def service_worker(request):
    """Service worker na raiz para scope «/»."""
    from django.contrib.staticfiles.finders import find

    path = find("home/js/sw.js")
    if not path:
        return HttpResponse(status=404)
    response = FileResponse(open(path, "rb"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def pedir_musica(request):
    pode_marcar = user_pode_marcar(request.user)
    context = {
        **_evento_pedidos_context(),
        "pode_marcar": pode_marcar,
        "vapid_public_key": vapid_public_key() if pode_marcar else "",
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


def sobre(request):
    context = {
        "sobre_pagina": SobrePagina.get_solo(),
        "nav_active": "sobre",
    }
    return render(request, "home/sobre.html", context)


def contato(request):
    config = ConfiguracaoHome.get_solo()
    form = ContatoForm()

    if request.method == "POST":
        form = ContatoForm(request.POST)
        if form.is_valid():
            ok, erro = enviar_mensagem_contato(form.cleaned_data, config)
            if ok:
                messages.success(
                    request,
                    "Mensagem enviada com sucesso. Responderemos em breve.",
                )
                return HttpResponseRedirect(reverse("home:contato"))
            messages.error(
                request,
                "Não foi possível enviar a mensagem. Tente novamente mais tarde.",
            )

    context = {
        "config_home": config,
        "contatos": Contato.objects.filter(ativo=True),
        "form": form,
        "nav_active": "contato",
    }
    return render(request, "home/contato.html", context)


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
        transaction.on_commit(
            lambda musica=pedido.musica, artista=pedido.artista, pk=pedido.pk: notificar_novo_pedido(
                musica=musica,
                artista=artista,
                pedido_id=pk,
            )
        )
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
            form.cleaned_data["motivo_rejeicao"],
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
        evento.pedidos.select_related("marcado_por", "motivo_rejeicao")
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


def _payload_inscricao_push(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None
    endpoint = (data.get("endpoint") or "").strip()
    keys = data.get("keys") or {}
    p256dh = (keys.get("p256dh") or "").strip()
    auth = (keys.get("auth") or "").strip()
    if not endpoint or not p256dh or not auth:
        return None
    return {
        "endpoint": endpoint[:URL_MAX_LENGTH],
        "p256dh": p256dh[:200],
        "auth": auth[:200],
        "user_agent": (request.META.get("HTTP_USER_AGENT") or "")[:300],
    }


@require_POST
@login_required
def push_inscrever(request):
    if not user_pode_marcar(request.user):
        raise PermissionDenied
    payload = _payload_inscricao_push(request)
    if not payload:
        return JsonResponse({"ok": False, "error": "Subscrição inválida."}, status=400)
    InscricaoPush.objects.update_or_create(
        endpoint=payload["endpoint"],
        defaults={
            "user": request.user,
            "p256dh": payload["p256dh"],
            "auth": payload["auth"],
            "user_agent": payload["user_agent"],
        },
    )
    return JsonResponse({"ok": True})


@require_POST
@login_required
def push_desinscrever(request):
    if not user_pode_marcar(request.user):
        raise PermissionDenied
    payload = _payload_inscricao_push(request)
    endpoint = (payload or {}).get("endpoint") or ""
    if not endpoint:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = {}
        endpoint = (data.get("endpoint") or "").strip()
    if endpoint:
        InscricaoPush.objects.filter(endpoint=endpoint, user=request.user).delete()
    else:
        InscricaoPush.objects.filter(user=request.user).delete()
    return JsonResponse({"ok": True})
